from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from clinicApp.app.api.address.dao import AddressDAO
from clinicApp.app.api.auth.dao import UsersDAO
from clinicApp.app.api.doctor_leaves.dao import DoctorLeavesDao
from clinicApp.app.api.doctor_leaves.schema import DoctorLeaveAllSchema
from clinicApp.app.api.doctors.dao import DoctorsDAO
from clinicApp.app.api.doctors.schemas import DoctorResponseSchema, DoctorUpdateSchema, DoctorDashboardSchema
from clinicApp.app.api.medical_cards.dao import MedicalCardsDAO
from clinicApp.app.api.medical_cards.schema import MedicalCardResponseSchema

router = APIRouter(prefix='/doctors', tags=['doctor'])

@router.get("/", summary="Получить всех врачей", response_model=list[DoctorResponseSchema])
async def get_all_doctors():
    doctors= await DoctorsDAO.get_full_data()
    return doctors

@router.get('/get_data', summary="Получить врача по id", response_model=DoctorResponseSchema)
async def get_doctor(doctor_id: int = Query(...)):
    doctor = await DoctorsDAO.get_by_id(doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "Пользователь не найден"
        )
    return doctor

@router.post('/add_doctor', summary='Добавить врача')
async def add_doctor(doctor_data: DoctorUpdateSchema) -> dict:
    existing_user = await UsersDAO.find_one_or_none(login=doctor_data.users.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь уже существует"
        )

    await DoctorsDAO.add_doctor(doctor_data)
    return {"message": "Врач успешно добавлен!"}

@router.delete("/delete")
async def dell_student_by_id(doctor_id: int = Query(...)) -> dict:
    check = await DoctorsDAO.delete_doctor_by_id(doctor_id=doctor_id)
    if check:
        return {"message": f"Врач с ID {doctor_id} удален!"}
    else:
        return {"message": "Ошибка при удалении Врача!"}

@router.put("/update")
async def update_doctors(data: DoctorUpdateSchema, doctor_id: int = Query(...)) -> dict:

    user_id, address_id, education_id = await DoctorsDAO.update_doctor(doctor_id, data)
    if data.users and user_id:
        await UsersDAO.update(user_id, data.users.model_dump(exclude_unset=True))

    if data.addresses and address_id:
        await AddressDAO.update(address_id, data.addresses.model_dump(exclude_unset=True))

    if data.education and education_id:
        await DoctorsDAO.update_education(education_id, data.education.model_dump(exclude_unset=True))

    return {"message": "Данные врача успешно обновлены"}

@router.get("/dashboard", response_model=DoctorDashboardSchema)
async def doctor_dashboard(doctor_id: int = Query(...)):
    return await DoctorsDAO.get_doctor_dashboard_data(int(doctor_id))

@router.get("/patientsCards",  response_model=list[MedicalCardResponseSchema], summary='Список всех его записей в картах его пациентов')
async def get_patient_cards(doctor_id: int = Query(...)):
    return await MedicalCardsDAO.get_cards_for_doctor(doctor_id)

@router.get("/leaves/search", response_model=list[DoctorLeaveAllSchema])
async def search_leaves(
    doctor_id: int,
    from_date: Optional[date] = Query(None, description="Дата начала периода"),
    to_date: Optional[date] = Query(None, description="Дата конца периода"),
    statuse: Optional[str] = Query(None, description="Статус отпуска"),
    reason: Optional[str] = Query(None, description="Причина отпуска"),
):
    leaves = await DoctorLeavesDao.search_leaves(doctor_id, None, from_date, to_date, statuse, reason)
    return leaves

@router.get("/admin/search/", response_model=list[DoctorResponseSchema], summary='Поиск по врачам')
async def search_patient(doctor_name: Optional[str] = Query(None), department: Optional[str] = Query(None)):
    return await DoctorsDAO.search_patients(doctor_name, department)