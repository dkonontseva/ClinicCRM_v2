import asyncio
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import uvicorn
from aiokafka import AIOKafkaProducer
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

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
from clinicApp.core.database import async_session_maker
from clinicApp.models.models import Talons, Users, Doctors
from clinicApp.core.email import send_email

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


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    return templates.TemplateResponse("adminDashboard.html", {"request": request})


# === Manage Users (Doctors / Patients) ===

@app.get("/admin/doctors", response_class=HTMLResponse)
async def admin_doctor_list(request: Request):
    return templates.TemplateResponse("doctorsList.html", {"request": request})

@app.get("/admin/patients", response_class=HTMLResponse)
async def admin_patient_list(request: Request):
    return templates.TemplateResponse("patientsList.html", {"request": request})

@app.get("/admin/editUser/{user_id}", response_class=HTMLResponse)
async def admin_edit_user(request: Request, user_id: int):
    return templates.TemplateResponse("editPatient.html", {"request": request, "user_id": user_id})

# === Schedule Management ===

@app.get("/admin/schedule", response_class=HTMLResponse)
async def admin_schedule(request: Request):
    return templates.TemplateResponse("scheduleList.html", {"request": request})

@app.get("/admin/editSchedule/{schedule_id}", response_class=HTMLResponse)
async def admin_edit_schedule(request: Request, schedule_id: int):
    return templates.TemplateResponse("editSchedule.html", {"request": request, "schedule_id": schedule_id})

# === Leave Management ===

@app.get("/admin/leaves", response_class=HTMLResponse)
async def admin_leaves(request: Request):
    return templates.TemplateResponse("doctorLeaves.html", {"request": request})

@app.get("/admin/editLeave/{leave_id}", response_class=HTMLResponse)
async def admin_edit_leave(request: Request, leave_id: int):
    return templates.TemplateResponse("editLeaves.html", {"request": request, "leave_id": leave_id})

# === Medical Records Management ===

@app.get("/admin/medicalCards", response_class=HTMLResponse)
async def admin_medical_cards(request: Request):
    return templates.TemplateResponse("doctors/medicalCardsForPatient.html", {"request": request})

@app.get("/admin/medicalCard/{card_id}", response_class=HTMLResponse)
async def admin_medical_card_detail(request: Request, card_id: int):
    return templates.TemplateResponse("doctors/medicalCard.html", {"request": request, "card_id": card_id})

# === Admin Chat & Video Room ===

@app.get("/admin/chat", response_class=HTMLResponse)
async def admin_chat(request: Request):
    return templates.TemplateResponse("doctors/chat.html", {"request": request})

@app.get("/admin/video", response_class=HTMLResponse)
async def admin_video(request: Request):
    return templates.TemplateResponse("doctors/video.html", {"request": request})

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

scheduler = AsyncIOScheduler()

async def send_appointment_reminders():
    async with async_session_maker() as session:
        tomorrow = datetime.now().date() + timedelta(days=1)
        
        query = (
            select(
                Users.login.label('patient_email'),
                Doctors.users.has(Users.first_name).label('doctor_first_name'),
                Doctors.users.has(Users.last_name).label('doctor_last_name'),
                Talons.date,
                Talons.time
            )
            .join(Users, Talons.patient_id == Users._id)
            .join(Doctors, Talons.doctor_id == Doctors._id)
            .where(Talons.date == tomorrow)
            .where(Talons.status == 'approved')
        )
        
        result = await session.execute(query)
        appointments = result.all()
        
        for appointment in appointments:
            subject = "Напоминание о записи к врачу"
            body = f"""
            <html>
                <body>
                    <h2>Уважаемый пациент!</h2>
                    <p>Напоминаем о вашей записи к врачу:</p>
                    <ul>
                        <li>Дата: {appointment.date}</li>
                        <li>Время: {appointment.time}</li>
                        <li>Врач: {appointment.doctor_last_name} {appointment.doctor_first_name}</li>
                    </ul>
                    <p>С уважением,<br>Ваша клиника</p>
                </body>
            </html>
            """
            
            await send_email(
                subject=subject,
                recipients=[appointment.patient_email],
                body=body
            )

scheduler.add_job(
    send_appointment_reminders,
    CronTrigger(hour=7, minute=0),
    id='appointment_reminders',
    replace_existing=True
)

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

    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Остановка Kafka producer...")
    await producer.stop()
    print("✅ Producer остановлен.")
    
    # Отменяем все фоновые задачи
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

    scheduler.shutdown()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
