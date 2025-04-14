import uvicorn
from fastapi import FastAPI
from aiAssistant.app.api.router import router as chat_router

app = FastAPI(openapi_url="/api/v1/assistant/openapi.json", docs_url="/api/v1/assistant/docs")

app.include_router(chat_router, prefix="/api/v1/assistant")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)