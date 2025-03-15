from datetime import date
from typing import Optional, List

from pydantic import BaseModel, EmailStr

from clinicApp.app.schemas.schemas import BaseSchema, UserSchema, AddressSchema, DepartmentSchema, EducationSchema, TalonSchema


class DoctorResponseSchema(BaseModel):
    _id: int
    start_date: date
    birthday: date
    users: UserSchema
    addresses: AddressSchema
    departments: DepartmentSchema


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

class EducationUpdateSchema(BaseModel):
    university: Optional[str] = None
    faculty: Optional[str] = None
    speciality: Optional[str] = None


class DoctorUpdateSchema(BaseSchema):
    start_date: Optional[date] = None
    birthday: Optional[date] = None
    department_id: Optional[int] = None
    users: Optional[UserUpdateSchema]=None
    addresses: Optional[AddressUpdateSchema] = None
    education: Optional[EducationUpdateSchema] =None

class DoctorDashboardSchema(BaseModel):
    total_patients: int
    today_patients: int
    total_appointments: int
    upcoming_appointments: List[TalonSchema]
    today_appointments: List[TalonSchema]