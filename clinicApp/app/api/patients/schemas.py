from datetime import date
from typing import Optional

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
