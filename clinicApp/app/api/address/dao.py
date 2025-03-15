from fastapi import HTTPException
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError

from clinicApp.app.api.dao import BaseDAO
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Addresses


class AddressDAO(BaseDAO):
    model = Addresses

    @classmethod
    async def update(cls, address_id: int, update_data: dict):
        async with async_session_maker() as session:
            async with session.begin():
                query = select(cls.model).filter_by(_id=address_id)
                result = await session.execute(query)
                address = result.scalar_one_or_none()

                if not address:
                    raise HTTPException(status_code=404, detail="Адрес не найден")

                for key, value in update_data.items():
                    setattr(address, key, value)

                await session.commit()

                return {"message": "Данные пользователя успешно обновлены"}