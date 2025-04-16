import asyncio
import json
import os
from datetime import datetime

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from fastapi import APIRouter, Query, HTTPException
from redis import asyncio as aioredis
from select import select
from sqlalchemy import select

from aiAssistant.app.api import schemas, models
from aiAssistant.app.core.database import async_session_maker
from aiAssistant.ml.training.predict import vectorizer, model, predict_specialist_and_recommendation

router = APIRouter(prefix="/assistant", tags=["AI assistant"])


response_futures = {}

redis_client = aioredis.from_url("redis://redis:6379", db=0)
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
REQUEST_TOPIC = os.getenv("REQUEST_TOPIC", "appointment_requests")
RESPONSE_TOPIC = os.getenv("RESPONSE_TOPIC", "appointment_responses")
CONFIRMATION_TOPIC = os.getenv("CONFIRMATION_TOPIC", "appointment_confirmations")
ERROR_TOPIC = os.getenv("ERROR_TOPIC", "appointment_errors")

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

        # Сохраняем активную жалобу в Redis
        await redis_client.setex(
            f"active_complaint:{complaint.patient_id}",
            3600,  # TTL 1 час
            str(db_complaint.id)
        )
        print(f"💾 Saved active complaint {db_complaint.id} for patient {complaint.patient_id}")

        # Сохраняем специальность в Redis
        await redis_client.setex(
            f"specialty:{db_complaint.id}",
            3600,  # TTL 1 час
            specialist
        )
        print(f"💾 Saved specialty {specialist} for complaint {db_complaint.id}")

        db_recommendation = models.Recommendations(
            complaint_id=db_complaint.id,
            recommended_doctor_specialty=specialist,
            recommendation_text=recommendations,
            appointment_offered=False
        )
        session.add(db_recommendation)
        await session.commit()
        await session.refresh(db_recommendation)
        print(f"💡 Created recommendation for complaint {db_complaint.id}")

        return {
            "recommended_doctor_specialty": specialist,
            "recommendation_text": recommendations,
            "message": "Хотите подобрать ближайшую запись?",
            "appointment_offered": False
        }

@router.post("/search-appointment/", response_model=schemas.RecommendationsOutput)
async def search_appointment(patient_id: int = Query(..., gt=0)):
    async with async_session_maker() as session:
        # Получаем последнюю активную жалобу из Redis
        active_complaint = await redis_client.get(f"active_complaint:{patient_id}")
        if not active_complaint:
            raise HTTPException(status_code=404, detail="Активная жалоба не найдена")
        
        complaint_id = int(active_complaint.decode('utf-8'))
        print(f"🔍 Поиск записи для жалобы {complaint_id}")

        # Получаем специальность из Redis
        specialty = await redis_client.get(f"specialty:{complaint_id}")
        if not specialty:
            raise HTTPException(status_code=404, detail="Специальность не найдена или истек срок хранения")
        
        specialty = specialty.decode('utf-8')
        print(f"👨‍⚕️ Специальность: {specialty}")

        # Получаем рекомендацию из базы
        query = select(models.Recommendations).where(
            models.Recommendations.complaint_id == complaint_id
        )
        result = await session.execute(query)
        recommendation = result.scalar_one_or_none()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Рекомендация не найдена")

        # Отправляем запрос на поиск талона
        request_data = {
            "complaint_id": complaint_id,
            "specialty": specialty
        }
        print(f"📤 Отправка запроса в Kafka: {request_data}")
        
        # Создаем Future для ожидания ответа
        response_future = asyncio.Future()
        
        # Сохраняем Future в глобальный словарь
        response_futures[complaint_id] = response_future
        print(f"📝 Создан Future для жалобы {complaint_id}")
        
        try:
            await producer.send_and_wait(REQUEST_TOPIC, json.dumps(request_data).encode("utf-8"))
            print("✅ Запрос успешно отправлен в Kafka")
            
            # Ждем ответа с таймаутом
            try:
                print(f"⏳ Ожидание ответа для жалобы {complaint_id}...")
                response = await asyncio.wait_for(response_future, timeout=30.0)
                print(f"✅ Получен ответ: {response}")
                
                return {
                    "recommended_doctor_specialty": specialty,
                    "recommendation_text": recommendation.recommendation_text,
                    "message": f"Доктор {response['doctor']}, дата {response['date']}, время {response['time']}. Подтвердить запись?",
                    "appointment_offered": True,
                    "doctor_id": response["doctor_id"],
                    "date": response["date"],
                    "time": response["time"]
                }
            except asyncio.TimeoutError:
                print(f"❌ Таймаут ожидания ответа для жалобы {complaint_id}")
                return {
                    "recommended_doctor_specialty": specialty,
                    "recommendation_text": recommendation.recommendation_text,
                    "message": "К сожалению, сейчас нет доступных записей. Попробуйте позже.",
                    "appointment_offered": False
                }
        except Exception as e:
            print(f"❌ Ошибка при отправке запроса в Kafka: {e}")
            raise
        finally:
            # Удаляем Future из словаря
            if complaint_id in response_futures:
                del response_futures[complaint_id]
                print(f"🗑️ Удален Future для жалобы {complaint_id}")

async def wait_for_kafka(bootstrap_servers: str, max_retries: int = 20, retry_delay: int = 5):
    """Ожидание готовности Kafka"""
    for i in range(max_retries):
        try:
            consumer = AIOKafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                group_id=f"health_check_{i}",
                auto_offset_reset="earliest",
                enable_auto_commit=False
            )
            await consumer.start()
            # Пробуем получить метаданные кластера
            topics = await consumer.topics()
            print(f"Available topics: {topics}")
            await consumer.stop()
            print("Successfully connected to Kafka")
            return True
        except Exception as e:
            print(f"Attempt {i+1}/{max_retries} failed: {e}")
            if i < max_retries - 1:
                await asyncio.sleep(retry_delay)
    return False

async def consume_responses():
    """Постоянный consumer для ответов от сервиса клиники"""
    print("Запуск consumer для ответов от сервиса клиники...")
    
    # Ждем готовности Kafka
    if not await wait_for_kafka(KAFKA_BOOTSTRAP_SERVERS):
        print("❌Не удалось подключиться к Kafka после нескольких попыток")
        return
    
    consumer = AIOKafkaConsumer(
        RESPONSE_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="assistant_group",
        auto_offset_reset="latest",
        enable_auto_commit=True
    )
    
    try:
        await consumer.start()
        async for message in consumer:
            try:
                response = json.loads(message.value.decode("utf-8"))
                complaint_id = response.get("complaint_id")
                
                if "doctor" in response:  # Это ответ со слотом
                    print(f"Получен слот для жалобы {complaint_id}")
                    # Сохраняем в Redis для последующего получения через API
                    await redis_client.setex(
                        f"slot:{complaint_id}",
                        300,  # TTL 5 минут
                        json.dumps(response)
                    )
                    
                    # Обновляем статус рекомендации
                    async with async_session_maker() as session:
                        query = select(models.Recommendations).where(
                            models.Recommendations.complaint_id == complaint_id
                        )
                        result = await session.execute(query)
                        recommendation = result.scalar_one_or_none()
                        if recommendation:
                            recommendation.appointment_offered = True
                            await session.commit()
                    
                    # Устанавливаем результат в Future, если он существует
                    if complaint_id in response_futures:
                        future = response_futures[complaint_id]
                        if not future.done():
                            future.set_result(response)
                            print(f"✅ Future установлен для жалобы {complaint_id}")
                
                elif "message" in response:  # Это ответ о подтверждении
                    print(f"Получен ответ о подтверждении для жалобы {complaint_id}")
                    # Обновляем статус жалобы
                    async with async_session_maker() as session:
                        query = select(models.Complaints).where(
                            models.Complaints.id == complaint_id
                        )
                        result = await session.execute(query)
                        complaint = result.scalar_one_or_none()
                        if complaint:
                            complaint.status = "confirmed"
                            await session.commit()
                
                await consumer.commit()
            except Exception as e:
                print(f"❌ Ошибка при обработке ответа: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка при запуске consumer: {e}")
        raise
    finally:
        await consumer.stop()

@router.get("/consume-appointment-response/")
async def consume_appointment_response(complaint_id: int):
    """Эндпоинт для получения найденного слота"""
    slot_data = await redis_client.get(f"slot:{complaint_id}")
    if not slot_data:
        return {"message": "Нет доступных записей"}
    
    slot = json.loads(slot_data)
    return {
        "message": f"Доктор {slot['doctor']}, дата {slot['date']}, время {slot['time']}. Подтвердить запись?",
        "complaint_id": complaint_id,
        "doctor": slot["doctor"],
        "date": slot["date"],
        "time": slot["time"]
    }

@router.post("/confirm-appointment/")
async def confirm_appointment(complaint_id: int, confirmed: bool, patient_id: int):
    """Подтверждение записи"""
    if confirmed:
        slot_data = await redis_client.get(f"slot:{complaint_id}")
        if not slot_data:
            return {"message": "Предложенное время больше недоступно."}

        slot = json.loads(slot_data)
        
        appointment_date = datetime.strptime(slot["date"], "%Y-%m-%d").date()
        appointment_time = datetime.strptime(slot["time"], "%H:%M").time()

        # Создаем запись в базе ассистента
        db_appointment = models.AppointmentRequests(
            patient_id=patient_id,
            complaint_id=complaint_id,
            doctor_id=slot["doctor_id"],
            preferred_date=appointment_date,
            preferred_time=appointment_time,
            status="confirmed"
        )
        # Отправляем подтверждение в клинику
        confirmation = {
            "complaint_id": complaint_id,
            "patient_id": patient_id,
            "doctor_id": slot["doctor_id"],
            "date": slot["date"],
            "time": slot["time"],
            "confirmed": confirmed
        }

        try:
            await producer.send_and_wait(
                CONFIRMATION_TOPIC,
                json.dumps(confirmation).encode("utf-8")
            )
            async with async_session_maker() as session:
                session.add(db_appointment)
                await session.commit()
            return {"message": "Запись подтверждена!"}
        except Exception as e:
            print(f"Ошибка при отправке подтверждения через Kafka: {e}")
            raise    
    else:
        await redis_client.delete(f"slot:{complaint_id}")
        return {"message": "Запись отменена."}
