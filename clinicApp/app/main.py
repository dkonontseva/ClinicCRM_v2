import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clinicApp.app.api.auth.router import router as auth_router
from clinicApp.app.api.patients.router import router as patients_router
from clinicApp.app.api.doctors.router import router as doctors_router
from clinicApp.app.api.medical_cards.router import router as medcard_router
from clinicApp.app.api.doctor_leaves.router import router as leaves_router
from clinicApp.app.api.schedule.router import router as schedule_router
from clinicApp.app.api.talons.router import router as talons_router
from clinicApp.app.api.chat.router_socket import router as chat_router

app = FastAPI(openapi_url="/api/v1/clinic/openapi.json", docs_url="/api/v1/clinic/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(doctors_router)
app.include_router(medcard_router)
app.include_router(leaves_router)
app.include_router(schedule_router)
app.include_router(talons_router)
app.include_router(chat_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
