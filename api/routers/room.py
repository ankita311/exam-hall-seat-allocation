from fastapi import APIRouter, HTTPException
from api.schema import RoomCreate
from fastapi.responses import JSONResponse
import datetime
import json
from pathlib import Path

router=APIRouter(prefix="")

ROOMS_DIR = Path("data/rooms")
ROOMS_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/")
def read_root():
    return {"message": "Hello, World!"}


@router.post("/add-room")
async def add_room(room: RoomCreate):
    """
    Add a room with seating configuration.
    Stores the room data in a neat JSON structure for later use.
    """
    try:
        # Validate inputs
        if room.rows <= 0 or room.cols <= 0 :
            raise HTTPException(
                status_code=400,
                detail="rows andcols must be positive integers"
            )
        
        # Calculate total capacity
        total_capacity = room.rows * room.cols * 2
        
        # Create structured JSON data
        room_data = {
            "room_name": room.room_name,
            "created_at": datetime.now().isoformat(),
            "configuration": {
                "rows": room.rows,
                "cols": room.cols,
                "total_capacity": total_capacity
            },
            "layout": {
                "total_rows": room.rows,
                "total_columns": room.cols,
                "seats_per_bench": 2
            }
        }
        
        # Save to JSON file (sanitize room_name for filename)
        safe_room_name = "".join(c for c in room.room_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_room_name = safe_room_name.replace(' ', '_')
        json_filename = f"{safe_room_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        json_filepath = ROOMS_DIR / json_filename
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(room_data, f, indent=2, ensure_ascii=False)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": f"Room '{room.room_name}' added successfully",
                "room_name": room.room_name,
                "total_capacity": total_capacity,
                "file_saved": str(json_filepath),
                "data": room_data
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error adding room: {str(e)}"
        )

@router.get("/rooms")
def list_rooms():
    """List all stored room data files"""
    json_files = list(ROOMS_DIR.glob("*.json"))
    
    rooms = []
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                rooms.append({
                    "room_name": data.get("room_name"),
                    "created_at": data.get("created_at"),
                    "total_capacity": data.get("configuration", {}).get("total_capacity"),
                    "file": json_file.name
                })
        except Exception:
            continue
    
    return {
        "total_rooms": len(rooms),
        "rooms": sorted(rooms, key=lambda x: x.get("created_at", ""), reverse=True)
    }

@router.get("/rooms/{room_name}")
def get_room_data(room_name: str):
    """Retrieve data for a specific room by name"""
    json_files = list(ROOMS_DIR.glob(f"{room_name}*.json"))
    
    if not json_files:
        raise HTTPException(status_code=404, detail=f"Room '{room_name}' not found")
    
    # Get the most recent file for this room
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)

