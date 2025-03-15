from datetime import datetime

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, BOOLEAN, Date, Time
from sqlalchemy.orm import relationship

from aiAssistant.app.core.database import Base


class Complaints(Base):
    __tablename__ = 'complaints'

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(Integer, nullable=False)
    symptoms = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String, default='pending')

    recommendations = relationship('Recommendations', back_populates='complaints')
    appointment_requests = relationship('AppointmentRequests', back_populates='complaints')


class Recommendations(Base):
    __tablename__ = 'recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey('complaints.id', ondelete='CASCADE'), nullable=False)
    recommended_doctor_specialty = Column(String, nullable=False)
    recommendation_text = Column(String, nullable=False)
    appointment_offered = Column(BOOLEAN, default=False)

    complaints = relationship("Complaints", back_populates="recommendations")


class AppointmentRequests(Base):
    __tablename__ = 'appointment_requests'

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(Integer, ForeignKey('complaints.id'), nullable=False)
    patient_id = Column(Integer, nullable=False)
    doctor_id = Column(Integer, nullable=False)
    preferred_date = Column(Date, nullable=False)
    preferred_time = Column(Time, nullable=False)
    status = Column(String, default='pending')

    complaints = relationship("Complaints", back_populates="appointment_requests")


class TrainingData(Base):
    __tablename__ = 'training_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    symptoms = Column(String, nullable=False)
    recommended_specialty = Column(String, nullable=False)
    confirmed_specialty = Column(String)
    created_at = Column(DateTime, default=datetime.now)
