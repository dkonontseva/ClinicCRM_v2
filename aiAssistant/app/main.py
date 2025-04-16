import asyncio

import uvicorn
from fastapi import FastAPI
from aiAssistant.app.api.router import router as chat_router, consume_responses, producer
from aiAssistant.app.core.kafka import ensure_topics_exist, wait_for_kafka

app = FastAPI(openapi_url="/api/v1/assistant/openapi.json", docs_url="/api/v1/assistant/docs")

app.include_router(chat_router, prefix="/api/v1/assistant")

# Хранилище для фоновых задач
background_tasks = set()

@app.on_event("startup")
async def startup_event():
    print("🔄 Ожидание Kafka...")
    if not await wait_for_kafka():
        print("❌ Не удалось подключиться к Kafka")
        return
        
    print("📡 Обеспечение существования Kafka топиков...")
    await ensure_topics_exist()
    
    print("📡 Запуск Kafka producer...")
    await producer.start()
    print("✅ Producer запущен. Запуск задачи consumer...")
    
    # Создаем и сохраняем фоновую задачу
    task = asyncio.create_task(consume_responses())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    
    print("🔁 Kafka consumer запущен в фоновом режиме.")

@app.on_event("shutdown")
async def shutdown_event():
    print("🛑 Остановка Kafka producer...")
    await producer.stop()
    print("✅ Producer остановлен.")
    
    # Отменяем все фоновые задачи
    for task in background_tasks:
        task.cancel()
    await asyncio.gather(*background_tasks, return_exceptions=True)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)