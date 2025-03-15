from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy.future import select
from datetime import datetime

from clinicApp.app.api.chat.clientManager import ConnectionManager
from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import ChatMessages, Doctors, Users, Departments

router = APIRouter(prefix="/chat", tags=["Chat"])
manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(
        websocket: WebSocket, doctor_id: int
):
    async with async_session_maker() as session:
        # Определяем отделение врача
        result = await session.execute(
            select(Doctors)
            .options(selectinload(Doctors.departments), selectinload(Doctors.users))
            .where(Doctors._id == doctor_id)
        )
        doctor = result.scalar_one_or_none()

        if not doctor or not doctor.departments:
            await websocket.close(code=1008, reason="Doctor or department not found")
            return

        department_name = doctor.departments.department_name
        sender_name = f"{doctor.users.first_name} {doctor.users.last_name}"

        # Подключаем врача к чату его отделения
        await manager.connect(websocket, department_name, doctor_id)

        # Отправляем историю сообщений
        messages = await session.execute(
            select(ChatMessages)
            .where(ChatMessages.doctor_id == doctor_id)
            .order_by(ChatMessages.timestapm.asc())
        )

        for msg in messages.scalars():
            await websocket.send_json({
                "msg": msg.message,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "sender": sender_name,
                "isSender": msg.doctor_id == doctor_id
            })

        # Уведомляем о подключении
        await manager.broadcast(f"{sender_name} присоединился к чату.", department_name, doctor_id, sender_name,
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        try:
            while True:
                data = await websocket.receive_text()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # Сохраняем сообщение в БД
                new_message = ChatMessages(
                    doctor_id=doctor_id,
                    message=data,
                    timestapm=datetime.now()
                )
                session.add(new_message)
                await session.commit()

                # Рассылаем сообщение участникам
                await manager.broadcast(data, department_name, doctor_id, sender_name, timestamp)

        except WebSocketDisconnect:
            manager.disconnect(department_name, doctor_id)
            await manager.broadcast(f"{sender_name} покинул чат.", department_name, doctor_id, sender_name,
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@router.get("/{department_name}")
async def get_chat_history(department_name: str):
    async with async_session_maker() as session:
        result = await session.execute(
            select(ChatMessages)
            .join(ChatMessages.doctors)
            .join(Doctors.departments)
            .where(Departments.department_name == department_name)
            .order_by(ChatMessages.timestapm.asc())
            .options(joinedload(ChatMessages.doctors).joinedload(Doctors.users))
        )
        messages = result.scalars().all()

        return [
            {
                "msg": msg.message,
                "timestamp": msg.timestapm.strftime("%Y-%m-%d %H:%M:%S"),
                "sender": f"{msg.doctors.users.first_name} {msg.doctors.users.last_name}",
            }
            for msg in messages
        ]