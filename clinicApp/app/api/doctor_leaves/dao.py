from datetime import date
from typing import Optional

from sqlalchemy import select, delete, and_, or_
from sqlalchemy.orm import joinedload

from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import DoctorLeaves, Doctors, Users


class DoctorLeavesDao:

    model = DoctorLeaves

    @classmethod
    async def add_doctor_leave(cls, doctor_id: int, leave_data):
        async with async_session_maker() as session:
            new_leave = DoctorLeaves(
                doctor_id=doctor_id,
                leave_type=leave_data.leave_type,
                from_date=leave_data.from_date,
                to_date=leave_data.to_date,
                reason=leave_data.reason,
                status="Pending",
            )
            session.add(new_leave)
            await session.commit()
            return new_leave

    @classmethod
    async def delete_doctor_leave(cls, leave_id: int):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=leave_id)
                result = await session.execute(query)
                leave_to_delete = result.scalar_one_or_none()

                if not leave_to_delete:
                    return None

                await session.execute(
                    delete(cls.model).filter_by(_id=leave_to_delete._id)
                )

                await session.commit()
                return leave_id

    @classmethod
    async def update_doctor_leave_request(cls, leave_id: int, leave_data):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=leave_id)
                result = await session.execute(query)
                leave_to_update = result.scalar_one_or_none()
                if not leave_to_update:
                    return None

                for key, value in leave_data.dict(exclude_unset=True).items():
                    setattr(leave_to_update, key, value)

                await session.commit()
                return {"message": "Leave request updated successfully"}

    @classmethod
    async def get_leaves_for_doctor(cls, doctor_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(doctor_id=doctor_id)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_leave_by_id(cls, leave_id: int):
        async with async_session_maker() as session:
            query = select(cls.model).join(Doctors).join(Users).options(joinedload(cls.model.doctors)).filter_by(_id=leave_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def get_all_leaves(cls):
        async with async_session_maker() as session:
            query = select(cls.model).join(Doctors).join(Users).options(joinedload(cls.model.doctors))
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def search_leaves(
            cls, doctor_id: Optional[int] = None, full_name: Optional[str] = None, from_date: Optional[date] = None,
            to_date: Optional[date] = None, status: Optional[str] = None, leave_type: Optional[str] = None
    ):
        async with async_session_maker() as session:
            query = select(cls.model).join(Doctors).join(Users).options(joinedload(cls.model.doctors))

            filters = []

            if doctor_id is not None:
                filters.append(Doctors._id == doctor_id)

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
            if from_date:
                filters.append(cls.model.from_date >= from_date)
            if to_date:
                filters.append(cls.model.to_date <= to_date)
            if status:
                filters.append(cls.model.status == status)
            if leave_type:
                filters.append(cls.model.leave_type.ilike(f"%{leave_type}%"))

            if filters:
                query = query.where(and_(*filters))

            result = await session.execute(query)
            return result.scalars().all()

