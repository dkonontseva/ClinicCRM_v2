from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, delete, and_, or_, func, distinct
from sqlalchemy.orm import joinedload

from clinicApp.app.api.auth.auth import get_password_hash
from clinicApp.app.api.dao import BaseDAO
from clinicApp.app.api.doctors.schemas import DoctorUpdateSchema
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Users, Addresses, Doctors, Education, Talons, Departments, Services


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
    async def update_doctor(cls, doctor_id: int, request: DoctorUpdateSchema):
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
            # Получаем общее количество пациентов
            total_patients_query = select(func.count(distinct(Talons.patient_id))).where(Talons.doctor_id == doctor_id)
            total_patients = await session.scalar(total_patients_query)

            # Получаем количество пациентов на сегодня
            today = datetime.now().date()
            today_patients_query = select(func.count(distinct(Talons.patient_id))).where(
                and_(Talons.doctor_id == doctor_id, Talons.date == today)
            )
            today_patients = await session.scalar(today_patients_query)

            # Получаем общее количество записей
            total_appointments_query = select(func.count(Talons._id)).where(Talons.doctor_id == doctor_id)
            total_appointments = await session.scalar(total_appointments_query)

            # Получаем предстоящие записи
            upcoming_appointments_query = (
                select(
                    Talons,
                    Services.service,
                    Services.price
                )
                .outerjoin(Services, Talons.service_id == Services._id)
                .where(
                    and_(
                        Talons.doctor_id == doctor_id,
                        Talons.date >= today,
                        Talons.status != "declined"
                    )
                )
                .order_by(Talons.date, Talons.time)
            )
            result = await session.execute(upcoming_appointments_query)
            upcoming_appointments_list = [
                {
                    "id": row.Talons._id,
                    "date": row.Talons.date,
                    "time": row.Talons.time,
                    "status": row.Talons.status,
                    "patient_id": row.Talons.patient_id,
                    "doctor_id": row.Talons.doctor_id,
                    "service_id": row.Talons.service_id if row.Talons.service_id is not None else 0,
                    "service": row.service if hasattr(row, 'service') and row.service else None,
                    "price": row.price if hasattr(row, 'price') and row.price else None
                }
                for row in result.all()
            ]

            # Получаем записи на сегодня с информацией об услугах
            today_appointments_query = (
                select(
                    Talons,
                    Services.service,
                    Services.price
                )
                .outerjoin(Services, Talons.service_id == Services._id)
                .where(
                    and_(
                        Talons.doctor_id == doctor_id,
                        Talons.date == today,
                        Talons.status != "declined"
                    )
                )
                .order_by(Talons.time)
            )
            result = await session.execute(today_appointments_query)
            today_appointments_list = [
                {
                    "id": row.Talons._id,
                    "date": row.Talons.date,
                    "time": row.Talons.time,
                    "status": row.Talons.status,
                    "patient_id": row.Talons.patient_id,
                    "doctor_id": row.Talons.doctor_id,
                    "service_id": row.Talons.service_id if row.Talons.service_id is not None else 0,
                    "service": row.service if hasattr(row, 'service') and row.service else None,
                    "price": row.price if hasattr(row, 'price') and row.price else None
                }
                for row in result.all()
            ]

            return {
                "total_patients": total_patients or 0,
                "today_patients": today_patients or 0,
                "total_appointments": total_appointments or 0,
                "upcoming_appointments": upcoming_appointments_list,
                "today_appointments": today_appointments_list
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

    @classmethod
    async def search_doctors_by_name(cls, name: str):
        async with async_session_maker() as session:
            search_parts = name.split()
            query = select(Doctors._id.label("id"), Users.first_name, Users.last_name, Users.second_name) \
                .join(Users, Doctors.user_id == Users._id)

            conditions = []
            for part in search_parts:
                conditions.append(
                    or_(
                        Users.first_name.ilike(f"%{part}%"),
                        Users.last_name.ilike(f"%{part}%"),
                        Users.second_name.ilike(f"%{part}%")
                    )
                )

            query = query.where(and_(*conditions))
            result = await session.execute(query)
            return result.mappings().all()

    @classmethod
    async def get_doctor_name_by_id(cls, doctor_id: int):
        async with async_session_maker() as session:
            query = select(Doctors._id.label("id"), Users.first_name, Users.last_name, Users.second_name
                           ).join(Users,Doctors.user_id == Users._id
                                  ).where(Doctors._id == doctor_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_department(cls):
        async with async_session_maker() as session:
            query = select(Departments.department_name.label("name"))
            result = await session.execute(query)
            return result.scalars().all()
