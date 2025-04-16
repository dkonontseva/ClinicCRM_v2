from typing import Optional
from datetime import time, date, datetime

from pydantic import BaseModel, validator


class AppointmentCreate(BaseModel):
    doctor_id: int
    date: str  # Дата в формате "YYYY-MM-DD"
    time: str  # Время в формате "HH:MM"
    service_id: int

    @validator('date')
    def validate_date(cls, v):
        try:
            # Проверяем, что строка соответствует формату даты
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Дата должна быть в формате YYYY-MM-DD")

class AvailableSlotsResponse(BaseModel):
    available_slots: list[str]

class DoctorAppointmentsResponse(BaseModel):
    _id: int
    last_name: str
    first_name: str
    second_name: str
    phone_number: str
    department: str

class AppointmentResponse(BaseModel):
    doctor_last_name: str
    doctor_first_name: str
    doctor_second_name: str
    patient_last_name: str
    patient_first_name: str
    patient_second_name: str
    date: date
    time: time
    status: str
    service: Optional[str] = None
    price: Optional[float] = None

    @classmethod
    def from_row(cls, row):
        return cls.model_validate(row._asdict())
    

class AppointmentResponseDoctor(BaseModel):
    patient_last_name: str
    patient_first_name: str
    patient_second_name: str
    date: date
    time: time
    status: str
    service: Optional[str] = None
    price: Optional[float] = None

    @classmethod
    def from_row(cls, row):
        return cls.model_validate(row._asdict())
    
class AppointmentResponsePatient(BaseModel):
    doctor_last_name: str
    doctor_first_name: str
    doctor_second_name: str
    date: date
    time: time
    status: str
    service: Optional[str] = None
    price: Optional[float] = None

    @classmethod
    def from_row(cls, row):
        return cls.model_validate(row._asdict())
    