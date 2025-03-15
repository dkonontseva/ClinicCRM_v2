from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select, delete, and_, or_

from clinicApp.app.api.schedule.schema import ScheduleResponse, ScheduleUpdate
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Schedules, Doctors, Departments, Shifts, Users
from clinicApp.app.schemas.schemas import ScheduleSchema


class ScheduleDAO:

    model = Schedules

    @classmethod
    async def get_all_schedules(cls):
        async with async_session_maker() as session:
            query = (
                select(
                    cls.model._id,
                    Users.last_name, Users.first_name, Users.second_name,
                    Departments.department_name,
                    Shifts.start_time, Shifts.end_time,
                    cls.model.day_of_week
                )
                .join(Doctors, cls.model.doctor_id == Doctors._id)
                .join(Users, Doctors.user_id == Users._id)
                .join(Shifts, cls.model.shift_id == Shifts._id)
                .join(Departments, Doctors.department_id == Departments._id)
                .order_by(Users.last_name, cls.model.day_of_week)
            )

            result = await session.execute(query)
            return [ScheduleResponse.from_row(row) for row in result.all()]

    @classmethod
    async def get_schedule_by_id(cls, doctor_id: int):
        async with async_session_maker() as session:
            query = (
                select(
                    cls.model._id,
                    Users.last_name, Users.first_name, Users.second_name,
                    Departments.department_name,
                    Shifts.start_time, Shifts.end_time,
                    cls.model.day_of_week
                )
                .join(Doctors, cls.model.doctor_id == Doctors._id)
                .join(Users, Doctors.user_id == Users._id)
                .join(Shifts, cls.model.shift_id == Shifts._id)
                .join(Departments, Doctors.department_id == Departments._id)
                .filter(cls.model._id==doctor_id)
                .order_by(Users.last_name, cls.model.day_of_week)
            )
            result = await session.execute(query)
            row = result.first()
            if not row:
                raise HTTPException(
                    status_code=404, detail="Расписание не найдено."
                )
            return ScheduleResponse.from_row(row) if row else None

    @classmethod
    async def add_schedule(cls, schedule: ScheduleSchema):
        async with async_session_maker() as session:
            db_schedule = cls.model(**schedule.dict())
            session.add(db_schedule)
            await session.commit()
            session.refresh(db_schedule)
            return db_schedule

    @classmethod
    async def update(cls, schedule_id: int, schedule):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=schedule_id)
                result = await session.execute(query)
                db_schedule = result.scalar_one_or_none()
                if not db_schedule:
                    return None

                for key, value in schedule.dict(exclude_unset=True).items():
                    setattr(db_schedule, key, value)

                await session.commit()
                return db_schedule

    @classmethod
    async def delete(cls, schedule_id: int):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=schedule_id)
                result = await session.execute(query)
                schedule_to_delete = result.scalar_one_or_none()

                if not schedule_to_delete:
                    return None

                await session.execute(
                    delete(cls.model).filter_by(_id=schedule_to_delete._id)
                )

                await session.commit()
                return schedule_id

    @classmethod
    async def search(cls, full_name: Optional[str] = None, department: Optional[str] = None, day_of_week: Optional[str] = None):
        async with async_session_maker() as session:
            query = (
                select(
                    cls.model._id,
                    Users.last_name, Users.first_name, Users.second_name,
                    Departments.department_name,
                    Shifts.start_time, Shifts.end_time,
                    cls.model.day_of_week
                )
                .join(Doctors, cls.model.doctor_id == Doctors._id)
                .join(Users, Doctors.user_id == Users._id)
                .join(Shifts, cls.model.shift_id == Shifts._id)
                .join(Departments, Doctors.department_id == Departments._id)
            )

            filters=[]
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

            if day_of_week:
                filters.append(Schedules.day_of_week.ilike(f"%{day_of_week}%"))

            if filters:
                query=query.where(and_(*filters))

            query = query.order_by(Users.last_name, cls.model.day_of_week)
            result = await session.execute(query)
            return [ScheduleResponse.from_row(row) for row in result.all()]
