import json
from datetime import datetime

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi import APIRouter, Query, HTTPException
from select import select
from redis import asyncio as aioredis

from aiAssistant.app.api import schemas, models
from aiAssistant.app.core.database import async_session_maker
from aiAssistant.ml.training.predict import vectorizer, model, predict_specialist_and_recommendation
from sqlalchemy import select

router = APIRouter(prefix="/assistant", tags=["AI assistant"])

redis_client = aioredis.from_url("redis://redis:6379", db=0)
KAFKA_BOOTSTRAP_SERVERS= "localhost:9092"
REQUEST_TOPIC = "appointment_requests"
RESPONSE_TOPIC = "appointment_responses"
CONFIRMATION_TOPIC = "appointment_confirmations"

producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

@router.get("/chat", response_model=list[schemas.ChatHistory])
async def get_complaints(patient_id: int = Query(..., gt=0)):
    async with async_session_maker() as session:
        query = (
            select(
                models.Complaints.id,
                models.Complaints.symptoms,
                models.Complaints.created_at,
                models.Complaints.status,
                models.Recommendations.recommended_doctor_specialty,
                models.Recommendations.recommendation_text,
                models.Recommendations.appointment_offered,
                models.AppointmentRequests.doctor_id,
                models.AppointmentRequests.preferred_date,
                models.AppointmentRequests.preferred_time,
            )
            .join(models.Recommendations, models.Recommendations.complaint_id == models.Complaints.id, isouter=True)
            .join(models.AppointmentRequests, models.AppointmentRequests.complaint_id == models.Complaints.id, isouter=True)
            .where(models.Complaints.patient_id == patient_id)
        )
        result = await session.execute(query)
        complaints = result.all()

        if not complaints:
            raise HTTPException(status_code=404, detail="Начните использовать вашего персонального ассистента!")

        response_data = []
        for row in complaints:
            (complaint_id, symptoms, created_at, status,
             recommended_doctor_specialty, recommendation_text, appointment_offered,
             doctor_id, preferred_date, preferred_time) = row

            response_data.append(schemas.ChatHistory(
                complaint_id=complaint_id,
                symptoms=symptoms,
                created_at=created_at,
                status=status,
                recommendations=schemas.RecommendationsOutput(
                    recommended_doctor_specialty=recommended_doctor_specialty or "",
                    recommendation_text=recommendation_text or "",
                    appointment_offered=appointment_offered,
                ),
                appointment_requests=schemas.AppointmentRequestOutput(
                    doctor_id=doctor_id,
                    preferred_date=preferred_date,
                    preferred_time=preferred_time,
                ) if doctor_id is not None else None
            ))

        return response_data


@router.post("/complaints/", response_model=schemas.RecommendationsOutput)
async def create_complaint(complaint: schemas.ComplaintsInput):
    async with async_session_maker() as session:
        symptoms = complaint.symptoms

        # Преобразуем симптомы в числовые признаки
        symptoms_vector = vectorizer.transform([symptoms]).toarray()
    
        # Предсказываем специализацию врача
        specialist = model.predict(symptoms_vector)[0]
    
        # Получаем рекомендации
        recommendations = predict_specialist_and_recommendation(symptoms)

        db_complaint = models.Complaints(
            patient_id=complaint.patient_id,
            symptoms=symptoms,
            created_at=datetime.now(),
            status="pending"
        )
        session.add(db_complaint)
        await session.commit()
        await session.refresh(db_complaint)

        db_recommendation = models.Recommendations(
            complaint_id=db_complaint.id,
            recommended_doctor_specialty=specialist,
            recommendation_text=recommendations,
            appointment_offered=False
        )
        session.add(db_recommendation)
        await session.commit()
        await session.refresh(db_recommendation)

        await producer.start()
        request_data = {
            "complaint_id": db_complaint.id,
            "specialty": specialist
        }
        await producer.send_and_wait(REQUEST_TOPIC, json.dumps(request_data).encode("utf-8"))
        await producer.stop()

        return {
            "recommended_doctor_specialty": specialist,
            "recommendation_text": recommendations,
            "message": "Хотите подобрать ближайшую запись?",
            "appointment_offered": False
        }


@router.get("/consume-appointment-response/")
async def consume_appointment_response():
    consumer = AIOKafkaConsumer(RESPONSE_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id="assistant_group")
    await consumer.start()
    try:
        async for message in consumer:
            response = json.loads(message.value.decode("utf-8"))
            doctor = response.get("doctor")
            date = response.get("date")
            time = response.get("time")
            complaint_id = response.get("complaint_id")

            return {
                "message": f"Доктор {doctor}, дата {date}, время {time}. Подтвердить запись?",
                "complaint_id": complaint_id,
                "doctor": doctor,
                "date": date,
                "time": time
            }
    finally:
        await consumer.stop()


@router.post("/confirm-appointment/")
async def confirm_appointment(complaint_id: int, confirmed: bool, patient_id: int):
    if confirmed:
        slot_data = await redis_client.get(f"slot:{complaint_id}")
        if not slot_data:
            return {"message": "Предложенное время больше недоступно."}

        slot_data = json.loads(slot_data)

        confirmation = {
            "complaint_id": complaint_id,
            "patient_id": patient_id,
            "doctor_id": slot_data["doctor_id"],
            "date": slot_data["date"],
            "time": slot_data["time"],
            "confirmed": confirmed
        }

        db_apppintment = models.AppointmentRequests(
            patient_id=patient_id,
            complaint_id=complaint_id,
            doctor_id=slot_data["doctor_id"],
            preferred_date=slot_data["date"],
            preferred_time=slot_data["time"],
            status="confirmed"
        )

        await producer.start()
        try:
            await producer.send_and_wait(CONFIRMATION_TOPIC, json.dumps(confirmation).encode("utf-8"))
            async with async_session_maker() as session:
                session.add(db_apppintment)
                await session.commit()
                await session.refresh(db_apppintment)
            return {"message": "Запись подтверждена!"}
        finally:
            await producer.stop()
    else:
        return {"message": "Запись отменена."}