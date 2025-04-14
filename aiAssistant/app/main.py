from fastapi import FastAPI
from aiAssistant.app.api.router import router as ai_router
app = FastAPI(openapi_url="/api/v1/assistant/openapi.json", docs_url="/api/v1/assistant/docs")

app.include_router(chat_router, prefix="/api/v1/assistant")

