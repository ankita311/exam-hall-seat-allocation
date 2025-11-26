from pydantic import BaseModel

class Student(BaseModel):
    id: int
    roll_no: str
    course: str