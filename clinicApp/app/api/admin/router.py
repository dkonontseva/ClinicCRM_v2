from fastapi import APIRouter

from clinicApp.app.api.admin.dao import AdminDAO
from clinicApp.app.api.admin.schemas import AdminDashboardSchema, VisitForecastResponse

router = APIRouter(
    prefix="/api/v1/clinic/admin",
    tags=["Admin"]
)

@router.get("/dashboard", response_model=AdminDashboardSchema)
async def get_admin_dashboard():
    return await AdminDAO.get_admin_dashboard_data()

@router.get("/forecast", response_model=VisitForecastResponse)
async def get_visit_forecast(
    months_ahead: int = 6,
):
    """
    Получение прогноза посещений на следующие месяцы
    
    Parameters:
    - months_ahead: количество месяцев для прогноза (по умолчанию 6)
    """
    forecasts = await AdminDAO.get_visit_forecast(months_ahead)
    return VisitForecastResponse(forecasts=forecasts)
