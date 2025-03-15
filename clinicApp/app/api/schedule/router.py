from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from clinicApp.app.api.schedule.dao import ScheduleDAO
from clinicApp.app.api.schedule.schema import ScheduleResponse, ScheduleUpdate
from clinicApp.app.schemas.schemas import ScheduleSchema

router = APIRouter(prefix='/schedule', tags=['Schedule'])

@router.get("/", response_model=list[ScheduleResponse])
async def get_all():
    return await ScheduleDAO.get_all_schedules()

@router.get("/getSchedule", response_model=ScheduleResponse, summary="Получить раасписания по id")
async def get_schedule_by_id(schedule_id: int = Query(...)):
    return await ScheduleDAO.get_schedule_by_id(schedule_id)

@router.post("/add")
async def add_schedule(schedule: ScheduleSchema):
    data = await ScheduleDAO.add_schedule(schedule)
    if not data:
        raise HTTPException(status_code=404, detail ="Возникла ошибка при добавлении расписания.")
    return data

@router.put("/update")
async def doctor_update_schedule(data: ScheduleUpdate, schedule_id: int = Query(...)):
    updated_leave = await ScheduleDAO.update(schedule_id, data)
    if not updated_leave:
        raise HTTPException(status_code=404, detail="Расписание не найдено или не может быть обновлено.")
    return {"message": "Расписание редактировано успешно!"}

@router.delete("/delete")
async def doctor_delete_schedule(schedule_id: int = Query(...)):
    check = await ScheduleDAO.delete(schedule_id)
    if not check:
        raise HTTPException(
            status_code=404,
            detail="Расписание не найдено."
        )
    return {"message": "Расписание удалено успешно!"}

@router.get("/admin/search", response_model=list[ScheduleResponse], summary='Поиск и фильтрация расписаний для админа')
async def search_schedules(full_name: Optional[str] = Query(None), department: Optional[str] = Query(None), day_of_week:Optional[str] = Query(None)):
    return await ScheduleDAO.search(full_name, department, day_of_week)