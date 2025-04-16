from datetime import date
from typing import Optional

from clinicApp.app.api.talons.schema import AppointmentResponsePatient
from fastapi import APIRouter, Depends, HTTPException, status, Query
from clinicApp.app.api.address.dao import AddressDAO
from clinicApp.app.api.auth.dao import UsersDAO
from clinicApp.app.api.medical_cards.dao import MedicalCardsDAO
from clinicApp.app.api.medical_cards.schema import MedicalCardResponseSchema
from clinicApp.app.api.patients.dao import PatientsDAO
from clinicApp.app.api.patients.schemas import PatientResponseSchema, PatientCreateSchema, PatientUpdateSchema, PatientDashboardSchema
from clinicApp.app.api.talons.dao import AppointmentsDAO
from clinicApp.app.schemas.schemas import TalonSchema

router = APIRouter(prefix='/patients', tags=['Patient'])

@router.get("/", summary="Получить всех пациентов", response_model=list[PatientResponseSchema])
async def get_all_patients():
    patients= await PatientsDAO.get_full_data()
    return patients

@router.get('/patient', summary="Получить пациента по id", response_model=PatientResponseSchema)
async def get_patient(id: int = Query(...)):
    patient = await PatientsDAO.get_by_id(int(id))
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    return patient

@router.post('/add_patient', summary='Добавить пациента')
async def add_patient(patient_data: PatientCreateSchema) -> dict:
    existing_user = await UsersDAO.find_one_or_none(login=patient_data.users.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь уже существует"
        )

    await PatientsDAO.add_patient(patient_data)
    return {"message": "Пациент успешно добавлен!"}

@router.delete("/delete/{patient_id}")
async def dell_student_by_id(patient_id: int) -> dict:
    check = await PatientsDAO.delete_patient_by_id(patient_id=patient_id)
    if check:
        return {"message": f"Пациент с ID {patient_id} удален!"}
    else:
        return {"message": "Ошибка при удалении Пациента!"}

@router.put("/update/{patient_id}")
async def update_patients(patient_id: int, request: PatientUpdateSchema) -> dict:

    user_id, address_id = await PatientsDAO.update_patient(patient_id, request)
    if request.users and user_id:
        await UsersDAO.update(user_id, request.users.model_dump(exclude_unset=True))

    if request.addresses and address_id:
        await AddressDAO.update(address_id, request.addresses.model_dump(exclude_unset=True))

    return {"message": "Данные пациента успешно обновлены"}

@router.get("/myCards", response_model = list[MedicalCardResponseSchema], summary='Список всех записей в картах конкретного пациента')
async def get_patient_cards(patient_id: int = Query(...)):
    return await MedicalCardsDAO.get_cards_for_patient(patient_id)


@router.get("/get_future_talon", response_model=list[AppointmentResponsePatient], summary='Список всех будущих визитов пациента')
async def get_for_patient(patient_id: int = Query(...)):
    return await AppointmentsDAO.get_for_patient(patient_id)

@router.get("/search/medical_cards", response_model=list[MedicalCardResponseSchema], summary='Поиск по мед картам для пациента')
async def get_patient_medical_cards(patient_name: str = Query(...)):
    return await MedicalCardsDAO.search(None, patient_name)

@router.get("/admin/search/", response_model=list[PatientResponseSchema], summary='Поиск по пациентам')
async def search_patient(patient_name: Optional[str] = Query(None)):
    return await PatientsDAO.search_patients(patient_name)

@router.get("/dashboard", response_model=PatientDashboardSchema)
async def get_patient_dashboard(patient_id: int = Query(...)):    
    return await PatientsDAO.get_patient_dashboard_data(patient_id)
