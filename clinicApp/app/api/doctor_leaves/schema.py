from datetime import date
from typing import Optional

from pydantic import BaseModel, computed_field


class DoctorLeaveUpdateSchema(BaseModel):
    _id: int
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    leave_type: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None

class DoctorLeaveAddSchema(BaseModel):
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    leave_type: Optional[str] = None
    reason: Optional[str] = None

class DoctorLeaveAllSchema(BaseModel):
    doctor_id: int
    leave_type: str
    from_date: date
    to_date: date
    reason: str
    status: str

    @computed_field
    @property
    def number_of_days(self) -> int:
        return (self.to_date - self.from_date).days + 1

