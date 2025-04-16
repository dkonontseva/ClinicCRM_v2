from typing import Optional
from datetime import datetime, date

from fastapi import HTTPException
from sqlalchemy import select, delete, update, and_, or_, func, extract
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from clinicApp.app.api.auth.auth import get_password_hash
from clinicApp.app.api.dao import BaseDAO
from clinicApp.app.api.patients.schemas import (
    PatientCreateSchema, 
    PatientUpdateSchema, 
    PatientDashboardSchema, 
    VisitByDepartment, 
    AppointmentHistory
)
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Patients, Users, Addresses, Talons, Doctors, Departments, Services


class PatientsDAO(BaseDAO):
    model = Patients

    @classmethod
    async def get_full_data(cls):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(joinedload(cls.model.users), joinedload(cls.model.addresses))
            )
            result = await session.execute(query)
            return result.scalars().all()


    @classmethod
    async def get_by_id(cls, patient_id: int):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .options(joinedload(cls.model.users), joinedload(cls.model.addresses))
                .filter_by(_id=patient_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def add_patient(cls, patient_data: PatientCreateSchema):
        async with async_session_maker() as session:
            async with session.begin():
                new_user = Users(
                    login=patient_data.users.login,
                    password=get_password_hash(patient_data.users.password),
                    first_name=patient_data.users.first_name,
                    last_name=patient_data.users.last_name,
                    second_name=patient_data.users.second_name,
                    phone_number=patient_data.users.phone_number,
                    gender=patient_data.users.gender,
                    role_id=1
                )
                session.add(new_user)
                await session.flush()

                new_address = Addresses(
                    country=patient_data.addresses.country,
                    city=patient_data.addresses.city,
                    street=patient_data.addresses.street,
                    house_number=patient_data.addresses.house_number,
                    flat_number=str(patient_data.addresses.flat_number)
                )
                session.add(new_address)
                await session.flush()

                new_patient = Patients(
                    b_date=patient_data.b_date,
                    user_id=new_user._id,
                    address_id=new_address._id
                )
                session.add(new_patient)

                await session.commit()
                return new_patient

    @classmethod
    async def delete_patient_by_id(cls, patient_id: int):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=patient_id)
                result = await session.execute(query)
                patient_to_delete = result.scalar_one_or_none()

                if not patient_to_delete:
                    return None

                await session.execute(
                    delete(Users).filter_by(_id=patient_to_delete.user_id)
                )

                await session.commit()
                return patient_id

    @classmethod
    async def update_patient(cls, patient_id:int, request: PatientUpdateSchema):
        async with async_session_maker() as session:
            query = (
                select(cls.model).filter_by(_id=patient_id)
            )
            result = await session.execute(query)
            patient = result.scalar_one_or_none()

            if not patient:
                raise HTTPException(
                    status_code=404,
                    detail="Пациент не найден"
                )
            user_id, address_id = patient.user_id, patient.address_id
            update_data = request.model_dump(exclude_unset=True, exclude={"users", "addresses"})
            for key, value in update_data.items():
                setattr(patient, key, value)
            await session.commit()
            await session.refresh(patient)
            return user_id, address_id

    @classmethod
    async def search_patients(cls, full_name: Optional[str]=None):
        async with async_session_maker() as session:
            query = (
                select(cls.model)
                .join(Users)
                .options(joinedload(cls.model.users), joinedload(cls.model.addresses))
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

            if filters:
                query = query.where(and_(*filters))

            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_patient_dashboard_data(cls, patient_id: int) -> PatientDashboardSchema:
        async with async_session_maker() as session:
            # Получаем следующую запись
            next_appointment_query = (
                select(Talons.date)
                .where(and_(Talons.patient_id == patient_id, Talons.date >= date.today()))
                .order_by(Talons.date)
                .limit(1)
            )
            next_appointment = await session.scalar(next_appointment_query)

            # Получаем общее количество записей
            total_records_query = select(func.count(Talons._id)).where(Talons.patient_id == patient_id)
            total_records = await session.scalar(total_records_query)

            # Получаем количество посещений по месяцам
            visits_by_month = [0] * 12
            visits_by_month_query = (
                select(
                    extract('month', Talons.date).label('month'),
                    func.count().label('count')
                )
                .where(Talons.patient_id == patient_id)
                .group_by('month')
            )
            result = await session.execute(visits_by_month_query)
            for row in result.all():
                month = int(row.month) - 1
                visits_by_month[month] = row.count

            # Получаем количество посещений по отделениям
            visits_by_department_query = (
                select(
                    Departments.department_name.label('department'),
                    func.count().label('count')
                )
                .select_from(Talons)
                .join(Doctors, Talons.doctor_id == Doctors._id)
                .join(Departments, Doctors.department_id == Departments._id)
                .where(Talons.patient_id == patient_id)
                .group_by(Departments.department_name)
            )
            result = await session.execute(visits_by_department_query)
            visits_by_department = [
                VisitByDepartment(department=row.department, count=row.count)
                for row in result.all()
            ]

            # Получаем предстоящие записи с информацией об услугах
            recent_appointments_query = (
                select(
                    Users.first_name.label('doctor_first_name'),
                    Users.last_name.label('doctor_last_name'),
                    Departments.department_name.label('department'),
                    Talons.date,
                    Talons.time,
                    Talons.status,
                    Services.service,
                    Services.price
                )
                .join(Doctors, Talons.doctor_id == Doctors._id)
                .join(Users, Doctors.user_id == Users._id)
                .join(Departments, Doctors.department_id == Departments._id)
                .outerjoin(Services, Talons.service_id == Services._id)
                .where(and_(Talons.patient_id == patient_id, Talons.date >= date.today()))
                .order_by(Talons.date, Talons.time)
            )
            result = await session.execute(recent_appointments_query)
            recent_appointments = [
                AppointmentHistory(
                    doctor_first_name=row.doctor_first_name,
                    doctor_last_name=row.doctor_last_name,
                    department=row.department,
                    date=row.date,
                    time=row.time,
                    status=row.status,
                    service=row.service if row.service else None,
                    price=row.price if row.price else None
                )
                for row in result.all()
            ]

            # Получаем историю записей с информацией об услугах
            appointment_history_query = (
                select(
                    Users.first_name.label('doctor_first_name'),
                    Users.last_name.label('doctor_last_name'),
                    Departments.department_name.label('department'),
                    Talons.date,
                    Talons.time,
                    Talons.status,
                    Services.service,
                    Services.price
                )
                .join(Doctors, Talons.doctor_id == Doctors._id)
                .join(Users, Doctors.user_id == Users._id)
                .join(Departments, Doctors.department_id == Departments._id)
                .outerjoin(Services, Talons.service_id == Services._id)
                .where(and_(Talons.patient_id == patient_id, Talons.date < date.today()))
                .order_by(Talons.date.desc(), Talons.time.desc())
            )
            result = await session.execute(appointment_history_query)
            appointment_history = [
                AppointmentHistory(
                    doctor_first_name=row.doctor_first_name,
                    doctor_last_name=row.doctor_last_name,
                    department=row.department,
                    date=row.date,
                    time=row.time,
                    status=row.status,
                    service=row.service if row.service else None,
                    price=row.price if row.price else None
                )
                for row in result.all()
            ]

            return PatientDashboardSchema(
                next_appointment=next_appointment,
                medical_records=total_records or 0,
                visits_by_month=visits_by_month,
                visits_by_department=visits_by_department,
                recent_appointments=recent_appointments,
                appointment_history=appointment_history
            )

