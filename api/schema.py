from pydantic import BaseModel
from typing import Optional


class RoomCreate(BaseModel):
    room_name: str
    rows: int
    cols: int


class AllocationRequest(BaseModel):
    class1_name: str
    class2_name: str
    room_name: str
    date: Optional[str] = None