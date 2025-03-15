from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, delete, update, and_, or_
from sqlalchemy.orm import contains_eager, joinedload

from clinicApp.app.api.auth.auth import get_password_hash
from clinicApp.app.api.dao import BaseDAO
from clinicApp.app.api.doctors.schemas import DoctorUpdateSchema
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Users, Addresses, Doctors, Education, Talons, Departments


class DoctorsDAO(BaseDAO):
    model = Doctors

    @classmethod
    async def get_full_data(cls):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(joinedload(cls.model.users), joinedload(cls.model.addresses),
                         joinedload(cls.model.departments), joinedload(cls.model.education))
            )
            result = await session.execute(query)
            return result.scalars().all()


    @classmethod
    async def get_by_id(cls, doctor_id: int):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(joinedload(cls.model.users), joinedload(cls.model.addresses),
                         joinedload(cls.model.departments), joinedload(cls.model.education))
                .filter_by(_id=doctor_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add_doctor(cls, doctor_data: DoctorUpdateSchema):
        async with async_session_maker() as session:
            async with session.begin():
                new_user = Users(
                    login=doctor_data.users.login,
                    password=get_password_hash(doctor_data.users.password),
                    first_name=doctor_data.users.first_name,
                    last_name=doctor_data.users.last_name,
                    second_name=doctor_data.users.second_name,
                    phone_number=doctor_data.users.phone_number,
                    gender=doctor_data.users.gender,
                    role_id=2
                )
                session.add(new_user)
                await session.flush()

                new_address = Addresses(
                    country=doctor_data.addresses.country,
                    city=doctor_data.addresses.city,
                    street=doctor_data.addresses.street,
                    house_number=doctor_data.addresses.house_number,
                    flat_number=doctor_data.addresses.flat_number
                )
                session.add(new_address)
                await session.flush()

                new_education = Education(
                    university=doctor_data.education.university,
                    faculty=doctor_data.education.faculty,
                    speciality=doctor_data.education.speciality,
                )
                session.add(new_education)
                await session.flush()

                new_doctor = Doctors(
                    start_date=doctor_data.start_date,
                    birthday=doctor_data.birthday,
                    department_id=doctor_data.department_id,
                    user_id=new_user._id,
                    address_id=new_address._id
                )
                session.add(new_doctor)

                await session.commit()
                return new_doctor

    @classmethod
    async def delete_doctor_by_id(cls, doctor_id: int):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=doctor_id)
                result = await session.execute(query)
                doctor_to_delete = result.scalar_one_or_none()

                if not doctor_to_delete:
                    return None

                await session.execute(
                    delete(Users).filter_by(_id=doctor_to_delete.user_id)
                )

                await session.commit()
                return doctor_id

    @classmethod
    async def update_doctor(cls, doctor_id:int, request: DoctorUpdateSchema):
        async with async_session_maker() as session:
            query = (
                select(cls.model).filter_by(_id=doctor_id)
            )
            result = await session.execute(query)
            doctor = result.scalar_one_or_none()

            if not doctor:
                raise HTTPException(
                    status_code=404,
                    detail="Врач не найден"
                )

            user_id, address_id, education_id = doctor.user_id, doctor.address_id, doctor.education_id
            update_data = request.model_dump(exclude_unset=True, exclude={"users", "addresses", "education"})
            for key, value in update_data.items():
                setattr(doctor, key, value)
            await session.commit()
            await session.refresh(doctor)
            return user_id, address_id, education_id

    @classmethod
    async def update_education(cls, education_id: int, update_data: dict):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(Education).filter_by(_id=education_id)
                result = await session.execute(query)
                education = result.scalar_one_or_none()

                if not education:
                    raise HTTPException(status_code=404, detail="Адрес не найден")

                for key, value in update_data.items():
                    setattr(education, key, value)

                await session.commit()

                return {"message": "Данные пользователя успешно обновлены"}

    @classmethod
    async def get_doctor_dashboard_data(cls, doctor_id: int):
        async with async_session_maker() as session:
            today = datetime.now().date()

            total_patients = await session.execute(
                select(Talons.patient_id).distinct().filter_by(doctor_id=doctor_id)
            )
            today_patients = await session.execute(
                select(Talons).filter_by(doctor_id=doctor_id, date=today)
            )
            total_appointments = await session.execute(
                select(Talons).filter_by(doctor_id=doctor_id)
            )
            upcoming_appointments = await session.execute(
                select(Talons)
                .filter(Talons.doctor_id == doctor_id, Talons.date >= today, Talons.status != "declined")
                .order_by(Talons.date, Talons.time)
            )
            today_appointments = await session.execute(
                select(Talons)
                .filter(Talons.doctor_id == doctor_id, Talons.date == today, Talons.status != "declined")
                .order_by(Talons.time)
            )

            return {
                "total_patients": len(total_patients.scalars().all()),
                "today_patients": len(today_patients.scalars().all()),
                "total_appointments": len(total_appointments.scalars().all()),
                "upcoming_appointments": upcoming_appointments.scalars().all(),
                "today_appointments": today_appointments.scalars().all(),
            }

    @classmethod
    async def search_patients(cls, full_name: Optional[str] = None, department: Optional[str] = None):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .join(Users)
                .options(joinedload(cls.model.users), joinedload(cls.model.addresses),
                         joinedload(cls.model.departments), joinedload(cls.model.education))
            )
            filters = []

            if full_name:
                name_parts = full_name.split()
                name_conditions = []

                if len(name_parts) == 3:
                    last_name, first_name, second_name = name_parts
                    name_conditions.append(or_(
                        Users.last_name.ilike(f"%{last_name}%"),
                        Users.first_name.ilike(f"%{first_name}%"),
                        Users.second_name.ilike(f"%{second_name}%")
                    ))
                elif len(name_parts) == 2:
                    first_name, last_name = name_parts
                    name_conditions.append(and_(
                        Users.first_name.ilike(f"%{first_name}%"),
                        Users.last_name.ilike(f"%{last_name}%")
                    ))
                else:
                    name_conditions.append(
                        Users.last_name.ilike(f"%{full_name}%")
                    )

                filters.append(and_(*name_conditions))

            if department:
                filters.append(Departments.department_name.ilike(f"%{department}%"))

            if filters:
                query = query.where(and_(*filters))

            result = await session.execute(query)
            return result.scalars().all()

