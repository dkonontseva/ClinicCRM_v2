from datetime import time
from typing import Optional

from pydantic import BaseModel



class ScheduleUpdate(BaseModel):
    shift_id: Optional[int]
    day_of_week: Optional[str]

class ScheduleResponse(BaseModel):
    _id: int
    first_name: str
    last_name: str
    second_name: str
    department_name: str
    start_time: time
    end_time: time
    day_of_week: str


    @classmethod
    def from_row(cls, row):
        return cls.model_validate(row._asdict())
