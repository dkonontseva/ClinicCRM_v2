from fastapi import APIRouter, Depends, HTTPException, status, Query

from clinicApp.app.api.medical_cards.dao import MedicalCardsDAO
from clinicApp.app.schemas.schemas import MedicalCardSchema

router = APIRouter(prefix='/medical_card', tags=['Medical Card'])

@router.get("/", response_model=MedicalCardSchema, summary="Получить всю информацию из одной записи в карте")
async def medical_record_doctor(record_id: int = Query(...)):
    record = await MedicalCardsDAO.get_medical_record_by_id(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Запись не найдена.")
    return record

@router.post("/add_note")
async def add_note(note: MedicalCardSchema, doctor_id: int = Query(...)):
    return await MedicalCardsDAO.add_medical_record(doctor_id, note)


