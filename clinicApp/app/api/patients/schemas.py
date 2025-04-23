from datetime import date, time
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from clinicApp.app.schemas.schemas import UserSchema, AddressSchema


class PatientResponseSchema(BaseModel):
    _id: int
    b_date: date
    users: UserSchema
    addresses: AddressSchema

    class Config:
        orm_mode = True


class PatientCreateSchema(BaseModel):
    b_date: date
    users: UserSchema
    addresses: AddressSchema


class UserUpdateSchema(BaseModel):
    login: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    second_name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    role_id: Optional[int] = None


class AddressUpdateSchema(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    flat_number: Optional[int] = None


class PatientUpdateSchema(BaseModel):
    b_date: Optional[date] = None
    users: Optional[UserUpdateSchema] = None
    addresses: Optional[AddressUpdateSchema] = None

    class Config:
        orm_mode = True


class VisitByDepartment(BaseModel):
    department: str
    count: int


class AppointmentHistory(BaseModel):
    doctor_first_name: str
    doctor_last_name: str
    department: str
    date: date
    time: time
    status: str
    service: Optional[str] = None
    price: Optional[float] = None


class PatientDashboardSchema(BaseModel):
    next_appointment: Optional[date]
    medical_records: int
    visits_by_month: List[int]
    visits_by_department: List[VisitByDepartment]
    recent_appointments: List[AppointmentHistory]
    appointment_history: List[AppointmentHistory]

class PatientShortSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    second_name: Optional[str]