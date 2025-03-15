from datetime import date

from pydantic import BaseModel



class MedicalCardResponseSchema(BaseModel):
    _id: int
    first_name: str
    last_name: str
    date: date





