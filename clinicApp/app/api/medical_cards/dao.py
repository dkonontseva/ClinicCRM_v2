from typing import Optional

from sqlalchemy import select, or_, and_

from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import MedicalCards, Patients, Doctors, Users

class MedicalCardsDAO:

    model = MedicalCards


    @classmethod
    async def add_medical_record(cls, doctor_id: int, note_data):
        async with async_session_maker() as session:
            new_note = MedicalCards(
                patient_id=note_data.patient_id,
                doctor_id=doctor_id,
                date=note_data.date,
                complaints=note_data.complaints,
                wellness_check=note_data.wellness_check,
                diagnosis=note_data.diagnosis,
            )
            session.add(new_note)
            await session.commit()
            return new_note


    @classmethod
    async def get_cards_for_doctor(cls, doctor_id: int):
        async with async_session_maker() as session:
            query = (
                select(
                    MedicalCards._id,
                    MedicalCards.date,
                    Users.first_name,
                    Users.last_name,
                    Users.second_name
                )
                .join(Patients, MedicalCards.patient_id == Patients._id)
                .join(Users, Patients.user_id == Users._id)
                .join(Doctors, MedicalCards.doctor_id == Doctors._id)
                .where(Doctors._id == doctor_id)
                .order_by(MedicalCards.date.desc())
            )
            result = await session.execute(query)
            return result.all()


    @classmethod
    async def get_cards_for_patient(cls,patient_id: int):
        async with async_session_maker() as session:
            query = (
                select(
                    MedicalCards._id,
                    MedicalCards.date,
                    Users.first_name,
                    Users.last_name
                )
                .join(Patients, Users._id == Patients.user_id)
                .join(MedicalCards, Patients._id == MedicalCards.patient_id)
                .join(Doctors, MedicalCards.doctor_id == Doctors._id)
                .where(Patients._id == patient_id)
                .order_by(MedicalCards.date.desc())
            )
            result = await session.execute(query)
            return [dict(row) for row in result.mappings()]

    @classmethod
    async def get_medical_record_by_id(cls,record_id: int):
        async with async_session_maker() as session:
            query = (
                select(MedicalCards, Patients, Doctors)
                .join(Patients, MedicalCards.patient_id == Patients._id)
                .join(Doctors, MedicalCards.doctor_id == Doctors._id)
                .filter(MedicalCards._id == record_id)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def search(cls, doctor_full_name: Optional[str], patient_full_name: Optional[str]):
        async with async_session_maker() as session:
            query = (
                select(
                    MedicalCards._id,
                    MedicalCards.date,
                    Users.first_name,
                    Users.last_name
                )
                .join(Patients, Users._id == Patients.user_id)
                .join(MedicalCards, Patients._id == MedicalCards.patient_id)
                .join(Doctors, MedicalCards.doctor_id == Doctors._id)
            )

            filters = []

            if doctor_full_name:
                name_parts = doctor_full_name.split()
                name_conditions = []

                if len(name_parts) == 3:
                    last_name, first_name, second_name = name_parts
                    name_conditions.append(or_(
                        Users.last_name.ilike(f"%{last_name}%"),
                        Users.first_name.ilike(f"%{first_name}%"),
                        Users.second_name.ilike(f"%{second_name}%")
                    ))
                elif len(name_parts) == 2:
                    last_name, first_name = name_parts
                    name_conditions.append(and_(
                        Users.first_name.ilike(f"%{first_name}%"),
                        Users.last_name.ilike(f"%{last_name}%")
                    ))
                else:
                    name_conditions.append(
                        Users.last_name.ilike(f"%{doctor_full_name}%")
                    )
                filters.append(and_(*name_conditions))

            if patient_full_name:
                name_parts = patient_full_name.split()
                name_conditions = []

                if len(name_parts) == 3:
                    last_name, first_name, second_name = name_parts
                    name_conditions.append(or_(
                        Users.last_name.ilike(f"%{last_name}%"),
                        Users.first_name.ilike(f"%{first_name}%"),
                        Users.second_name.ilike(f"%{second_name}%")
                    ))
                elif len(name_parts) == 2:
                    last_name, first_name = name_parts
                    name_conditions.append(and_(
                        Users.first_name.ilike(f"%{first_name}%"),
                        Users.last_name.ilike(f"%{last_name}%")
                    ))
                else:
                    name_conditions.append(
                        Users.last_name.ilike(f"%{patient_full_name}%")
                    )
                filters.append(and_(*name_conditions))

            if filters:
                query = query.where(and_(*filters))

            query = query.order_by(MedicalCards.date.desc())
            result = await session.execute(query)
            return [dict(row) for row in result.mappings()]


    # @classmethod
    # async def print_note()
