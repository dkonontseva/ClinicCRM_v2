from datetime import date
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from clinicApp.app.api.doctor_leaves.dao import DoctorLeavesDao
from clinicApp.app.api.doctor_leaves.schema import DoctorLeaveUpdateSchema, DoctorLeaveAddSchema, DoctorLeaveAllSchema

router = APIRouter(prefix='/doctor_leaves', tags=['Doctor Leaves'])

@router.post("/addLeave")
async def doctor_add_leave(leave: DoctorLeaveAddSchema, doctor_id: int = Query(...)):
    return await DoctorLeavesDao.add_doctor_leave(doctor_id, leave)

@router.delete("/delete")
async def delete_medical_record(leave_id: int = Query(...)):
    record = await DoctorLeavesDao.delete_doctor_leave(leave_id)
    if record:
        return {"message": "Заявка удалена успешно!"}

@router.get("/", response_model=list[DoctorLeaveAllSchema], summary="Получить все заявления для врача")
async def get_leaves_for_doctor(doctor_id: int = Query(...)):
    return await DoctorLeavesDao.get_leaves_for_doctor(doctor_id)


@router.get("/getLeave", response_model=DoctorLeaveAllSchema, summary="Получить заявление по id")
async def get_leave_by_id(leave_id: int = Query(...)):
    return await DoctorLeavesDao.get_leave_by_id(leave_id)

@router.get("/get_all", response_model=list[DoctorLeaveAllSchema], summary="Получить все заявления")
async def get_all_leaves():
    return await DoctorLeavesDao.get_all_leaves()

@router.put("/updateLeave")
async def doctor_update_leave(leave_data: DoctorLeaveUpdateSchema, leave_id: int = Query(...)):
    updated_leave = await DoctorLeavesDao.update_doctor_leave_request(leave_id, leave_data)
    if not updated_leave:
        raise HTTPException(status_code=404, detail="Заявка не найдена или не может быть обновлена.")
    return {"message": "Заявка редактирована успешно!"}

@router.get("/admin/leaves/search", response_model=list[DoctorLeaveAllSchema])
async def search_leaves(
    full_name: Optional[str] = Query(None, description="ФИО врача (например, Иванов Иван Иванович)"),
    from_date: Optional[date] = Query(None, description="Дата начала периода"),
    to_date: Optional[date] = Query(None, description="Дата конца периода"),
    status: Optional[str] = Query(None, description="Статус отпуска"),
    reason: Optional[str] = Query(None, description="Причина отпуска"),
):
    leaves = await DoctorLeavesDao.search_leaves(None, full_name, from_date, to_date, status, reason)
    return leaves

