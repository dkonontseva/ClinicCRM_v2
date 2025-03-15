import re
from datetime import date, time, datetime
from fastapi import HTTPException
from pydantic import Field, EmailStr, field_validator, computed_field, ConfigDict, BaseModel
from typing import Optional, List

from typing_extensions import Annotated

LETTER_MATCH_PATTERN = re.compile(r"^[а-яА-Яa-zA-Z\-]+$")


class BaseSchema(BaseModel):
    _id: Annotated[int, Field(gt=0)]

    model_config = ConfigDict(from_attributes=True)


class RoleSchema(BaseSchema):
    role: str

class UserSchema(BaseSchema):
    login: EmailStr = Field(min_length=3, max_length=100, description="Имя пользователя должно содержать от 3 до 100 символов")
    password: str = Field(min_length=8, description="пароль должен содержать от 8 до 30 символов")
    first_name: str = Field(min_length=3, max_length=100, description="Имя пользователя должно содержать от 3 до 100 символов")
    last_name: str = Field(min_length=3, max_length=100, description="Имя пользователя должно содержать от 3 до 100 символов")
    second_name: str = Field(default=None, min_length=3, max_length=100, description="Имя пользователя должно содержать от 3 до 100 символов")
    phone_number: str = Field(pattern = r"^\+375(29|33|44|25)\d{7}$", description="Номер телефона должен быть в формате +123456789")
    gender: str
    role_id: int

    @field_validator('first_name', mode='before')
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    @field_validator('last_name', mode='before')
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    @field_validator('second_name', mode='before')
    def validate_name(cls, value):
        if not LETTER_MATCH_PATTERN.match(value):
            raise HTTPException(
                status_code=422, detail="Name should contains only letters"
            )
        return value

    model_config = ConfigDict(from_attributes=True)

class UserAuthSchema(BaseModel):
    login: EmailStr = Field(min_length=3, max_length=100, description="Имя пользователя должно содержать от 3 до 100 символов")
    password: str = Field(min_length=8, max_length=30, description="пароль должен содержать от 8 до 30 символов")


class PatientSchema(BaseSchema):
    b_date: date
    user_id: int
    address_id: int


class DoctorSchema(BaseSchema):
    start_date: date
    birthday: date
    user_id: int
    address_id: int
    department_id: int


class AddressSchema(BaseSchema):
    country: str = Field(min_length=3, max_length=100)
    city: str = Field(min_length=3, max_length=100)
    street: str = Field(min_length=3, max_length=100)
    house_number: str = Field(min_length=1, max_length=3)
    flat_number: int = Field(gt=0)


class DepartmentSchema(BaseSchema):
    department_name: str = Field(min_length=3, max_length=100)


class ServiceSchema(BaseSchema):
    service: str = Field(min_length=3, max_length=100)
    price: float = Field(gt=1, lt=10000, description="Цена должна находится в пределах 1-10000 д. ед.")


class DoctorLeaveSchema(BaseSchema):
    from_date: date
    to_date: date
    leave_type: str = Field(min_length=3, max_length=100)
    reason: str = Field(min_length=20, max_length=200)
    status: str


class EducationSchema(BaseSchema):
    university: str = Field(min_length=3, max_length=50)
    faculty: str = Field(min_length=5, max_length=200)
    speciality: str = Field(min_length=8, max_length=200)


class MedicalCardSchema(BaseSchema):
    date: date
    complaints: str = Field(min_length=20, max_length=200)
    wellness_check: str = Field(min_length=20, max_length=300)
    diagnosis: str = Field(min_length=20, max_length=200)
    doctor_id: int
    patient_id: int


class ScheduleSchema(BaseSchema):
    day_of_week: str
    doctor_id: int
    shift_id: int


class ShiftSchema(BaseSchema):
    start_time: time
    end_time: time


class TalonSchema(BaseSchema):
    date: date
    time: time
    status: str
    patient_id: int
    doctor_id: int
    service_id: int


class ChatMessageSchema(BaseSchema):
    message: str
    timestapm: datetime
    user_id: int