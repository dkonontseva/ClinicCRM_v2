from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

class ComplaintsInput(BaseModel):
    patient_id: int
    symptoms: str


class RecommendationsOutput(BaseModel):
    recommended_doctor_specialty: str
    recommendation_text: str
    appointment_offered: bool
    warning: str = "ВНИМАНИЕ! Все рекомендации носят справочный характер. Помните, что обязательно необходимо проконсультироваться с врачом!"


class AppointmentRequestInput(BaseModel):
    complaint_id: int
    patient_id: int
    doctor_id: int
    preferred_date: date
    preferred_time: time

class AppointmentRequestOutput(BaseModel):
    doctor_id: int
    preferred_date: date
    preferred_time: time


class TrainingDataInput(BaseModel):
    symptoms: str
    recommended_specialty: str
    confirmed_specialty: Optional[str] = None


class ChatHistory(BaseModel):
    complaint_id: int
    symptoms: str
    created_at: datetime
    status: str
    recommendations: RecommendationsOutput
    appointment_requests: Optional[AppointmentRequestOutput] = None