import asyncio
import os
from datetime import date

import uvicorn
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clinicApp.app.api.auth.router import router as auth_router
from clinicApp.app.api.chat.router_socket import router as chat_router
from clinicApp.app.api.doctor_leaves.router import router as leaves_router
from clinicApp.app.api.doctors.router import router as doctors_router
from clinicApp.app.api.medical_cards.router import router as medcard_router
from clinicApp.app.api.patients.router import router as patients_router
from clinicApp.app.api.schedule.router import router as schedule_router
from clinicApp.app.api.talons.router import router as talons_router
from clinicApp.app.api.talons.dao import AppointmentsDAO
from clinicApp.app.core.kafka import ensure_topics_exist, wait_for_kafka
from clinicApp.app.api.admin import router as admin_router

app = FastAPI(openapi_url="/api/v1/clinic/openapi.json", docs_url="/api/v1/clinic/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/clinic")
app.include_router(patients_router, prefix="/api/v1/clinic")
app.include_router(doctors_router, prefix="/api/v1/clinic")
app.include_router(medcard_router, prefix="/api/v1/clinic")
app.include_router(leaves_router, prefix="/api/v1/clinic")
app.include_router(schedule_router, prefix="/api/v1/clinic")
app.include_router(talons_router, prefix="/api/v1/clinic")
app.include_router(chat_router, prefix="/api/v1/clinic")
app.include_router(admin_router, prefix="/api/v1/clinic")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")

producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

# Хранилище для фоновых задач
background_tasks = set()

@app.on_event("startup")
async def startup_event():
    print("🔄 Ожидание готовности Kafka...")
    if not await wait_for_kafka():
        print("❌ Ошибка подключения к Kafka")
        return
        
    print("📡 Обеспечение существования Kafka топиков...")
    await ensure_topics_exist()
    
    print("🚀 Запуск Kafka producer...")
    await producer.start()
    print("✅ Producer запущен. Запуск потребительских задач...")
    
    # Создаем и сохраняем фоновые задачи
    task1 = asyncio.create_task(AppointmentsDAO.consume_requests(date.today()))
    task2 = asyncio.create_task(AppointmentsDAO.consume_confirmations())
    
    # Сохраняем задачи, чтобы они не были уничтожены
    background_tasks.add(task1)
    background_tasks.add(task2)
    
    # Добавляем обратные вызовы для удаления задач из множества при их завершении
    task1.add_done_callback(background_tasks.discard)
    task2.add_done_callback(background_tasks.discard)
    
    print("🔁 Kafka consumers запущены в фоновом режиме.")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Остановка Kafka producer...")
    await producer.stop()
    print("✅ Producer остановлен.")
    
    # Отменяем все фоновые задачи
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
