from datetime import date, datetime

from pydantic import BaseModel



class MedicalCardResponseSchema(BaseModel):
    _id: int
    date: datetime
    first_name: str
    last_name: str

    class Config:
        from_attributes = True





