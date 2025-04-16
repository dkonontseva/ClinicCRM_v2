from datetime import date, time
from typing import List, Optional
from clinicApp.app.api.patients.schemas import VisitByDepartment
from pydantic import BaseModel


class RevenueByDepartment(BaseModel):
    department: str
    revenue: float


class AdminDashboardSchema(BaseModel):
    total_doctors: int
    total_patients: int
    today_appointments: int
    all_appointments: int
    visits_by_month: List[int]
    visits_by_department: List[VisitByDepartment]
    revenue_by_department: List[RevenueByDepartment]
    total_monthly_revenue: float


class VisitForecast(BaseModel):
    month: str
    year: int
    predicted_visits: int
    lower_bound: int
    upper_bound: int


class VisitForecastResponse(BaseModel):
    forecasts: List[VisitForecast]
    confidence_level: float = 0.95
