import os
from datetime import date
from typing import Optional

from aiokafka import AIOKafkaProducer
from fastapi import APIRouter, Query, HTTPException

from clinicApp.app.api.doctors.schemas import DoctorResponseSchema
from clinicApp.app.api.talons.dao import AppointmentsDAO
from clinicApp.app.api.talons.schema import AvailableSlotsResponse, AppointmentCreate, DoctorAppointmentsResponse, \
    AppointmentResponse
from clinicApp.app.schemas.schemas import TalonSchema

router = APIRouter(prefix='/appointments', tags=['Appointments'])

KAFKA_BOOTSTRAP_SERVERS =  os.getenv("KAFKA_BOOTSTRAP_SERVERS")

producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

@router.get("/get_all", response_model=list[AppointmentResponse], summary="Получить все записи")
async def find_appointments(doctor_name: Optional[str] = None, from_date: Optional[date] = None,
            to_date: Optional[date] = None, status: Optional[str] = None):
    return await AppointmentsDAO.find_all(doctor_name, from_date, to_date, status)

@router.get("/get_for_doctor", response_model=list[TalonSchema], summary='Получить для врача все будущие записи к нему')
async def get_talon(doctor_id: int = Query(...)):
    return await AppointmentsDAO.get_for_doctor(doctor_id)

@router.get("/slots", response_model=AvailableSlotsResponse)
async def get_available_slots(doctor_id: int, date: str):
    return await AppointmentsDAO.get_available_slots(doctor_id, date)


@router.post("/add", response_model=TalonSchema)
async def patient_book_appointment(data: AppointmentCreate, patient_id: int = Query(...), ):
    return await AppointmentsDAO.create_appointment(data, patient_id)


@router.put("/update", response_model=TalonSchema)
async def update_appointment(data: AppointmentCreate, appointment_id: int = Query(...)):
    updated_appointment = await AppointmentsDAO.update_appointment(appointment_id, data)
    if not updated_appointment:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return updated_appointment


@router.delete("/delete")
async def delete_appointment(appointment_id: int = Query(...)):
    result = await AppointmentsDAO.delete_appointment(appointment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    return result

@router.get("/", response_model=list[DoctorAppointmentsResponse], summary='Найти свободных врачей на выбранную дату')
async def get_doctors_for_appointments(
        patient_id: int,
        requested_date: str = Query(default=date.today()),
        department: str = Query(default=""),
        doctor_search: str = Query(default="")):
    return await AppointmentsDAO.find_appointments(patient_id, requested_date, department, doctor_search)

