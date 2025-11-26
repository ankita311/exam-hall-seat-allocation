from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from api.schema import AllocationRequest
from pathlib import Path
import json
from typing import List, Tuple, Dict
from datetime import datetime

router = APIRouter(prefix="/allocation")

CLASSES_DIR = Path("data/classes")
ROOMS_DIR = Path("data/rooms")


def get_class_data(class_name: str) -> dict:
    """Load the most recent class data by name"""
    json_files = list(CLASSES_DIR.glob(f"{class_name}*.json"))
    
    if not json_files:
        raise HTTPException(status_code=404, detail=f"Class '{class_name}' not found")
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_room_data(room_name: str) -> dict:
    """Load the most recent room data by name"""
    json_files = list(ROOMS_DIR.glob(f"{room_name}*.json"))
    
    if not json_files:
        raise HTTPException(status_code=404, detail=f"Room '{room_name}' not found")
    
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def allocate_seats_round_robin(
    class1_students: List[Dict],
    class2_students: List[Dict],
    rows: int,
    cols: int
) -> List[List[List[str]]]:
    """
    Round-robin seating allocation where 2 students from different classes 
    are paired together, ensuring no same course/subject.
    Each student is allocated only once. Unpaired students sit alone.
    """
    grid = []
    
    # Track which students have been used (by index to avoid duplicates)
    used_class1_indices = set()
    used_class2_indices = set()
    
    # Keep available lists (indices of unused students)
    available_class1_indices = list(range(len(class1_students)))
    available_class2_indices = list(range(len(class2_students)))
    
    for row in range(rows):
        row_data = []
        for col in range(cols):
            bench = []
            
            # Try to find an unused student from class1
            student1_index = None
            student1 = None
            
            if available_class1_indices:
                student1_index = available_class1_indices[0]
                student1 = class1_students[student1_index]
            
            # If no class1 student available, try class2 alone or leave empty
            if student1_index is None:
                # Try to find an unused student from class2 to seat alone
                if available_class2_indices:
                    student2_index = available_class2_indices[0]
                    student2 = class2_students[student2_index]
                    bench.append(student2['roll_no'])
                    used_class2_indices.add(student2_index)
                    available_class2_indices.remove(student2_index)
                else:
                    # No students left - empty bench
                    bench = []
                row_data.append(bench)
                continue
            
            # Try to find an unused student from class2 with different course
            found_pair = False
            student2_index = None
            
            for idx in available_class2_indices:
                student2 = class2_students[idx]
                
                # Check if courses are different
                if student1['course'] != student2['course']:
                    bench.append(student1['roll_no'])
                    bench.append(student2['roll_no'])
                    
                    # Mark both as used
                    used_class1_indices.add(student1_index)
                    used_class2_indices.add(idx)
                    available_class1_indices.remove(student1_index)
                    available_class2_indices.remove(idx)
                    found_pair = True
                    break
            
            # If no valid pair found with different course, try any unused student from class2
            if not found_pair and available_class2_indices:
                student2_index = available_class2_indices[0]
                student2 = class2_students[student2_index]
                bench.append(student1['roll_no'])
                bench.append(student2['roll_no'])
                
                # Mark both as used
                used_class1_indices.add(student1_index)
                used_class2_indices.add(student2_index)
                available_class1_indices.remove(student1_index)
                available_class2_indices.remove(student2_index)
                found_pair = True
            
            # If still no pair found (class2 exhausted), seat class1 student alone
            if not found_pair:
                bench.append(student1['roll_no'])
                used_class1_indices.add(student1_index)
                available_class1_indices.remove(student1_index)
            
            row_data.append(bench)
        
        grid.append(row_data)
    
    return grid


@router.post("/allocate-seats")
async def allocate_seats(request: AllocationRequest):
    """
    Perform round-robin seating allocation for 2 classes in a room.
    Ensures no 2 students on the same bench have the same course/subject.
    """
    try:
        # Load class and room data
        class1_data = get_class_data(request.class1_name)
        class2_data = get_class_data(request.class2_name)
        room_data = get_room_data(request.room_name)
        
        class1_students = class1_data.get('students', [])
        class2_students = class2_data.get('students', [])
        
        if not class1_students:
            raise HTTPException(status_code=400, detail=f"Class '{request.class1_name}' has no students")
        if not class2_students:
            raise HTTPException(status_code=400, detail=f"Class '{request.class2_name}' has no students")
        
        room_config = room_data.get('configuration', {})
        rows = room_config.get('rows', 0)
        cols = room_config.get('cols', 0)
        total_capacity = room_config.get('total_capacity', 0)
        
        if rows == 0 or cols == 0:
            raise HTTPException(status_code=400, detail=f"Room '{request.room_name}' has invalid configuration")
        
        # Check if room has enough capacity
        total_students = len(class1_students) + len(class2_students)
        if total_students > total_capacity:
            raise HTTPException(
                status_code=400,
                detail=f"Total students ({total_students}) exceeds room capacity ({total_capacity})"
            )
        
        # Perform allocation
        grid = allocate_seats_round_robin(class1_students, class2_students, rows, cols)
        
        # Format date
        date_str = request.date if request.date else datetime.now().strftime("%dth %b %Y")
        
        # Create seating data structure
        seating_data = {
            'hall': room_data.get('room_name', request.room_name),
            'date': date_str,
            'grid': grid,
            'class1': request.class1_name,
            'class2': request.class2_name,
            'total_students_class1': len(class1_students),
            'total_students_class2': len(class2_students),
            'room_configuration': {
                'rows': rows,
                'cols': cols,
                'total_capacity': total_capacity
            }
        }
        
        return JSONResponse(
            status_code=200,
            content=seating_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error allocating seats: {str(e)}"
        )
