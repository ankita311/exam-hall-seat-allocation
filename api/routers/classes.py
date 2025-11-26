
from pathlib import Path
import datetime
import json
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse


router=APIRouter(prefix="")

DATA_DIR = Path("data/classes")
DATA_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/add-class")
async def add_class(
    class_name: str =Form(...),
    file: UploadFile = File(...)
):
    """
    Upload an Excel file containing roll_no and course fields.
    Stores the data in a neat JSON structure for later use.
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400, 
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    try:
        # Read the Excel file into a pandas DataFrame
        df = pd.read_excel(await file.read())
        
        # Normalize column names (handle case-insensitive and whitespace)
        df.columns = df.columns.str.strip().str.lower()
        
        # Check if required columns exist
        required_columns = ['roll_no', 'course']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Available columns: {', '.join(df.columns.tolist())}"
            )
        
        # Extract and clean the data
        students_data = []
        for idx, row in df.iterrows():
            roll_no = str(row['roll_no']).strip() if pd.notna(row['roll_no']) else None
            course = str(row['course']).strip() if pd.notna(row['course']) else None
            
            # Skip rows with missing data
            if not roll_no or not course:
                continue
            
            students_data.append({
                "roll_no": roll_no,
                "course": course
            })
        
        if not students_data:
            raise HTTPException(
                status_code=400,
                detail="No valid student data found in the Excel file"
            )
        
        # Create structured JSON data
        class_data = {
            "class_name": class_name,
            "uploaded_at": datetime.datetime.now().isoformat(),
            "total_students": len(students_data),
            "students": students_data
        }
        
        # Sanitize class_name for filename
        safe_class_name = "".join(c for c in class_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_class_name = safe_class_name.replace(' ', '_')
        
        # Check if class already exists and delete old files
        existing_files = list(DATA_DIR.glob(f"{safe_class_name}_*.json"))
        is_replacement = len(existing_files) > 0
        
        if existing_files:
            # Delete all existing files for this class
            for old_file in existing_files:
                old_file.unlink()
        
        # Create new file with current timestamp
        json_filename = f"{safe_class_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_filepath = DATA_DIR / json_filename
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(class_data, f, indent=2, ensure_ascii=False)
        
        message = f"Class '{class_name}' {'replaced' if is_replacement else 'added'} successfully"
        
        return JSONResponse(
            status_code=200,
            content={
                "message": message,
                "class_name": class_name,
                "total_students": len(students_data),
                "file_saved": str(json_filepath),
                "replaced": is_replacement,
                "data": class_data
            }
        )
    
    except HTTPException:
        raise
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="The Excel file is empty")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/classes")
def list_classes():
    """List all stored class data files"""
    json_files = list(DATA_DIR.glob("*.json"))
    
    classes = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                classes.append({
                    "class_name": data.get("class_name"),
                    "uploaded_at": data.get("uploaded_at"),
                    "total_students": data.get("total_students"),
                    "file": json_file.name
                })
        except Exception:
            continue
    
    return {
        "total_classes": len(classes),
        "classes": sorted(classes, key=lambda x: x.get("uploaded_at", ""), reverse=True)
    }

@router.get("/classes/{class_name}")
def get_class_data(class_name: str):
    """Retrieve data for a specific class by name"""
    json_files = list(DATA_DIR.glob(f"{class_name}*.json"))
    
    if not json_files:
        raise HTTPException(status_code=404, detail=f"Class '{class_name}' not found")
    
    # Get the most recent file for this class
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)