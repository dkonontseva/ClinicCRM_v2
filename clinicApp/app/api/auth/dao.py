from fastapi import HTTPException
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError

from clinicApp.app.api.dao import BaseDAO
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Users


class UsersDAO(BaseDAO):
    model = Users

    @classmethod
    async def update(cls, user_id: int, update_data: dict):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=user_id)
                result = await session.execute(query)
                user = result.scalar_one_or_none()

                if not user:
                    raise HTTPException(status_code=404, detail="Пользователь не найден")

                for key, value in update_data.items():
                    setattr(user, key, value)

                await session.commit()

                return {"message": "Данные пользователя успешно обновлены"}