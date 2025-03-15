from typing import Optional

from pydantic import BaseModel
from datetime import time, date


class AppointmentCreate(BaseModel):
    doctor_id: int
    date: date
    time: time
    service_id: int

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

    @classmethod
    def from_row(cls, row):
        return cls.model_validate(row._asdict())