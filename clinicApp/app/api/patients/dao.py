from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, delete, update, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload

from clinicApp.app.api.auth.auth import get_password_hash
from clinicApp.app.api.dao import BaseDAO
from clinicApp.app.api.patients.schemas import PatientCreateSchema, PatientUpdateSchema
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Patients, Users, Addresses


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

