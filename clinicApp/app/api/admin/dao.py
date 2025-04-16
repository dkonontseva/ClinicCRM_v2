from datetime import date, timedelta
from sqlalchemy import select, func, extract, and_
import numpy as np
from typing import List
from collections import defaultdict

from clinicApp.app.core.database import async_session_maker
from clinicApp.app.models.models import Doctors, Patients, Talons, Departments, Services
from clinicApp.app.api.patients.schemas import VisitByDepartment
from clinicApp.app.api.admin.schemas import AdminDashboardSchema, VisitForecast, RevenueByDepartment


class AdminDAO:
    @classmethod
    async def get_admin_dashboard_data(cls) -> AdminDashboardSchema:
        async with async_session_maker() as session:
            # Get total doctors count
            total_doctors_query = select(func.count(Doctors._id))
            total_doctors = await session.scalar(total_doctors_query)

            # Get total patients count
            total_patients_query = select(func.count(Patients._id))
            total_patients = await session.scalar(total_patients_query)

            # Get today's appointments count
            today = date.today()
            today_appointments_query = (
                select(func.count(Talons._id))
                .where(Talons.date == today)
            )
            today_appointments = await session.scalar(today_appointments_query)

            # Get all appointments count
            all_appointments_query = select(func.count(Talons._id))
            all_appointments = await session.scalar(all_appointments_query)

            # Get visits by month
            visits_by_month = [0] * 12
            visits_by_month_query = (
                select(
                    extract('month', Talons.date).label('month'),
                    func.count().label('count')
                )
                .group_by('month')
            )
            result = await session.execute(visits_by_month_query)
            for row in result.all():
                month = int(row.month) - 1
                visits_by_month[month] = row.count

            # Get visits by department
            visits_by_department_query = (
                select(
                    Departments.department_name.label('department'),
                    func.count().label('count')
                )
                .select_from(Talons)
                .join(Doctors, Talons.doctor_id == Doctors._id)
                .join(Departments, Doctors.department_id == Departments._id)
                .group_by(Departments.department_name)
            )
            result = await session.execute(visits_by_department_query)
            visits_by_department = [
                VisitByDepartment(department=row.department, count=row.count)
                for row in result.all()
            ]

            # Получаем выручку по отделам за последний месяц
            first_day_of_month = date.today().replace(day=1)
            last_month = first_day_of_month - timedelta(days=1)
            first_day_of_last_month = last_month.replace(day=1)

            # Проверяем, есть ли данные за последний месяц
            check_data_query = (
                select(func.count(Talons._id))
                .where(
                    and_(
                        Talons.date >= first_day_of_last_month,
                        Talons.date < first_day_of_month,
                        Talons.service_id.isnot(None)
                    )
                )
            )
            has_data = await session.scalar(check_data_query)
            
            revenue_by_department = []
            total_monthly_revenue = 0.0
            
            if has_data:
                # Используем coalesce для предотвращения ошибок с NULL значениями
                revenue_by_department_query = (
                    select(
                        Departments.department_name.label('department'),
                        func.coalesce(func.sum(Services.price), 0).label('revenue')
                    )
                    .select_from(Talons)
                    .join(Doctors, Talons.doctor_id == Doctors._id)
                    .join(Departments, Doctors.department_id == Departments._id)
                    .outerjoin(Services, Talons.service_id == Services._id)  # Используем outerjoin вместо join
                    .where(
                        and_(
                            Talons.date >= first_day_of_last_month,
                            Talons.date < first_day_of_month,
                            Talons.service_id.isnot(None)  # Только записи с указанной услугой
                        )
                    )
                    .group_by(Departments.department_name)
                )
                result = await session.execute(revenue_by_department_query)
                revenue_by_department = [
                    RevenueByDepartment(department=row.department, revenue=float(row.revenue))
                    for row in result.all()
                ]

                # Получаем общую выручку за последний месяц
                total_revenue_query = (
                    select(func.coalesce(func.sum(Services.price), 0))
                    .select_from(Talons)
                    .outerjoin(Services, Talons.service_id == Services._id)  # Используем outerjoin вместо join
                    .where(
                        and_(
                            Talons.date >= first_day_of_last_month,
                            Talons.date < first_day_of_month,
                            Talons.service_id.isnot(None)  # Только записи с указанной услугой
                        )
                    )
                )
                total_monthly_revenue = await session.scalar(total_revenue_query) or 0.0
            
            # Добавим вывод для отладки
            print(f"Revenue by department: {revenue_by_department}")
            print(f"Total monthly revenue: {total_monthly_revenue}")

            return AdminDashboardSchema(
                total_doctors=total_doctors or 0,
                total_patients=total_patients or 0,
                today_appointments=today_appointments or 0,
                all_appointments=all_appointments or 0,
                visits_by_month=visits_by_month,
                visits_by_department=visits_by_department,
                revenue_by_department=revenue_by_department,
                total_monthly_revenue=float(total_monthly_revenue)
            )

    @classmethod
    async def get_visit_forecast(cls, months_ahead: int = 6) -> List[VisitForecast]:
        """
        Прогнозирование количества посещений на следующие месяцы с учетом сезонности
        """
        async with async_session_maker() as session:
            # Получаем исторические данные за последние 2 года
            two_years_ago = date.today() - timedelta(days=730)
            historical_data_query = (
                select(
                    extract('year', Talons.date).label('year'),
                    extract('month', Talons.date).label('month'),
                    func.count().label('visits')
                )
                .where(Talons.date >= two_years_ago)
                .group_by('year', 'month')
                .order_by('year', 'month')
            )
            result = await session.execute(historical_data_query)
            historical_data = result.all()

            if not historical_data:
                return []

            # Собираем данные по месяцам
            monthly_data = defaultdict(list)
            for row in historical_data:
                month = int(row.month)
                monthly_data[month].append(row.visits)

            # Вычисляем средние значения по месяцам
            monthly_avg = {}
            for month in range(1, 13):
                if month in monthly_data:
                    monthly_avg[month] = np.mean(monthly_data[month])
                else:
                    monthly_avg[month] = 0

            # Вычисляем общий тренд (средний рост/падение)
            total_months = len(historical_data)
            if total_months > 1:
                first_visits = sum(monthly_data[1]) if 1 in monthly_data else 0
                last_visits = sum(monthly_data[12]) if 12 in monthly_data else 0
                trend = (last_visits - first_visits) / total_months
            else:
                trend = 0

            # Создаем прогноз
            forecast = []
            current_date = date.today()
            
            for i in range(months_ahead):
                forecast_date = current_date + timedelta(days=30*i)
                month = forecast_date.month
                year = forecast_date.year
                
                # Базовый прогноз = среднее по месяцу + тренд
                base_forecast = monthly_avg[month] + (trend * i)
                
                # Защита от отрицательных значений
                base_forecast = max(0, base_forecast)
                
                # Вычисляем доверительные интервалы (20% от прогноза)
                margin = base_forecast * 0.1
                
                forecast.append(VisitForecast(
                    month=forecast_date.strftime("%B"),
                    year=year,
                    predicted_visits=int(round(base_forecast)),
                    lower_bound=int(round(max(0, base_forecast - margin))),
                    upper_bound=int(round(base_forecast + margin))
                ))
            
            return forecast 