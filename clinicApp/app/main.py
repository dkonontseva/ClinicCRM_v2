import asyncio
import os
from datetime import date
from pathlib import Path

import uvicorn
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

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

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Mount static files with proper configuration
app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Add URL processor for static files
templates.env.globals["url_for"] = lambda name, **params: f"/static/{params.get('filename', '')}"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/patientProfile", response_class=HTMLResponse)
async def patient_profile(request: Request):
    return templates.TemplateResponse("patients/profile.html", {"request": request})

@app.get("/patientDashboard", response_class=HTMLResponse)
async def patient_dashboard(request: Request):
    return templates.TemplateResponse("patients/dashboard.html", {"request": request})

@app.get("/findAppointment", response_class=HTMLResponse)
async def find_appointment(request: Request):
    return templates.TemplateResponse("patients/findAppointment.html", {"request": request})

@app.get("/myMedicalCard", response_class=HTMLResponse)
async def medical_card(request: Request):
    return templates.TemplateResponse("patients/medicalCard.html", {"request": request})

@app.get("/medicalCardNote/{note_id}", response_class=HTMLResponse)
async def medical_card_note(request: Request, note_id: int):
    return templates.TemplateResponse("patients/medicaCardNote.html", {"request": request, "note_id": note_id})

# Doctor routes
@app.get("/doctor/dashboard", response_class=HTMLResponse)
async def doctor_dashboard(request: Request):
    return templates.TemplateResponse("doctors/dashboard.html", {"request": request})

@app.get("/doctor/myLeaves", response_class=HTMLResponse)
async def doctor_leaves(request: Request):
    return templates.TemplateResponse("doctors/myLeaves.html", {"request": request})

@app.get("/doctor/patientsCards", response_class=HTMLResponse)
async def doctor_patients_cards(request: Request):
    return templates.TemplateResponse("doctors/patientsCards.html", {"request": request})

@app.get("/doctor/profile", response_class=HTMLResponse)
async def doctor_profile(request: Request):
    return templates.TemplateResponse("doctors/profile.html", {"request": request})

@app.get("/doctor/chat", response_class=HTMLResponse)
async def doctor_chat(request: Request):
    return templates.TemplateResponse("doctors/chat.html", {"request": request})

@app.get("/doctor/video", response_class=HTMLResponse)
async def doctor_video(request: Request):
    return templates.TemplateResponse("doctors/video.html", {"request": request})

@app.get("/doctor/create_room/{room_id}", response_class=HTMLResponse)
async def doctor_create_room(request: Request, room_id: str):
    return templates.TemplateResponse("doctors/room.html", {"request": request, "room_id": room_id})

@app.get("/doctor/join_room/{room_id}", response_class=HTMLResponse)
async def doctor_join_room(request: Request, room_id: str):
    return templates.TemplateResponse("doctors/room.html", {"request": request, "room_id": room_id})

@app.get("/doctor/add_note/{patient_id}", response_class=HTMLResponse)
async def doctor_add_note(request: Request, patient_id: int):
    return templates.TemplateResponse("doctors/notesPatient.html", {"request": request, "patient_id": patient_id})

@app.get("/doctor/medicalRecord/{record_id}", response_class=HTMLResponse)
async def doctor_medical_record(request: Request, record_id: int):
    return templates.TemplateResponse("doctors/medicalCard.html", {"request": request, "record_id": record_id})

@app.get("/doctor/addLeave", response_class=HTMLResponse)
async def doctor_add_leave(request: Request):
    return templates.TemplateResponse("doctors/editLeaves.html", {"request": request})

@app.get("/doctor/addLeave/{leave_id}", response_class=HTMLResponse)
async def doctor_edit_leave(request: Request, leave_id: int):
    return templates.TemplateResponse("doctors/editLeaves.html", {"request": request, "leave_id": leave_id})

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
