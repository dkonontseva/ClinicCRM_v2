from datetime import datetime

from sqlalchemy import Column, Integer, Time, DateTime, String, ForeignKey, SmallInteger, Float, Date
from sqlalchemy.orm import declarative_base, relationship

from clinicApp.app.core.database import engine, Base


class Roles(Base):
    __tablename__ = 'roles'

    id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False)
    users = relationship('Users', back_populates='roles')

class Users(Base):
    __tablename__ = 'users'

    _id = Column(Integer, primary_key=True)
    login = Column(String, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    second_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    gender = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'))
    patients = relationship('Patients', back_populates='users', uselist=False, passive_deletes=True)
    doctors = relationship('Doctors', back_populates='users', uselist=False)
    roles = relationship('Roles', back_populates='users')

class Patients(Base):
    __tablename__ = 'patients'

    _id = Column(Integer, primary_key=True)
    b_date = Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey('users._id', ondelete='CASCADE'), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses._id'))
    medical_cards = relationship('MedicalCards', back_populates='patients')
    talons = relationship('Talons', back_populates='patients')
    users = relationship('Users', back_populates='patients', uselist=False)
    addresses = relationship('Addresses', back_populates='patients')

class Doctors(Base):
    __tablename__ = 'doctors'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    start_date=Column(Date, nullable=False)
    birthday=Column(Date, nullable=False)
    user_id = Column(Integer, ForeignKey('users._id', ondelete='CASCADE'))
    address_id = Column(Integer, ForeignKey('addresses._id'))
    department_id = Column(Integer, ForeignKey('departments._id'))
    education_id = Column(Integer, ForeignKey('education._id'))
    users = relationship('Users', back_populates='doctors', uselist=False)
    addresses = relationship('Addresses', back_populates='doctors')
    departments = relationship('Departments', back_populates='doctors')
    education = relationship('Education', back_populates='doctors')
    doctor_leaves = relationship('DoctorLeaves', back_populates='doctors')
    medical_cards = relationship('MedicalCards', back_populates='doctors')
    talons = relationship('Talons', back_populates='doctors')
    schedules = relationship('Schedules', back_populates='doctors')
    chat_messages = relationship('ChatMessages', back_populates='doctors')

class Addresses(Base):
    __tablename__ = 'addresses'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    country = Column(String, nullable=False)
    city = Column(String, nullable=False)
    street = Column(String, nullable=False)
    house_number = Column(String, nullable=False)
    flat_number = Column(Integer, nullable=False)
    doctors = relationship('Doctors', back_populates='addresses')
    patients = relationship('Patients', back_populates='addresses')

class Departments(Base):
    __tablename__ = 'departments'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String, nullable=False)
    doctors = relationship('Doctors', back_populates='departments')


class Services(Base):
    __tablename__ = 'services'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    service = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    talons = relationship('Talons', back_populates='services')


class DoctorLeaves(Base):
    __tablename__ = 'doctor_leaves'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    leave_type = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors._id', ondelete='CASCADE'))
    doctors = relationship('Doctors', back_populates='doctor_leaves')


class Education(Base):
    __tablename__ = 'education'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    university = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    speciality = Column(String, nullable=False)
    doctors = relationship('Doctors', back_populates='education')


class MedicalCards(Base):
    __tablename__ = 'medical_cards'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    complaints = Column(String, nullable=False)
    wellness_check = Column(String, nullable=False)
    diagnosis = Column(String, nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors._id', ondelete='CASCADE'))
    doctors = relationship('Doctors', back_populates='medical_cards')
    patient_id = Column(Integer, ForeignKey('patients._id', ondelete='CASCADE'))
    patients = relationship('Patients', back_populates='medical_cards')


class Schedules(Base):
    __tablename__ = 'schedules'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(String, nullable=False)
    doctor_id = Column(Integer, ForeignKey('doctors._id'))
    shift_id = Column(Integer, ForeignKey('shifts._id'))
    doctors = relationship('Doctors', back_populates='schedules')
    shifts = relationship('Shifts', back_populates='schedules')


class Shifts(Base):
    __tablename__ = 'shifts'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    schedules = relationship('Schedules', back_populates='shifts')


class Talons(Base):
    __tablename__ = 'talons'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    status = Column(String, nullable=False)
    patient_id = Column(Integer, ForeignKey('patients._id', ondelete='CASCADE'))
    doctor_id = Column(Integer, ForeignKey('doctors._id', ondelete='CASCADE'))
    service_id = Column(Integer, ForeignKey('services._id'))
    patients = relationship('Patients', back_populates='talons')
    doctors = relationship('Doctors', back_populates='talons')
    services = relationship('Services', back_populates='talons')


class ChatMessages(Base):
    __tablename__ = 'chat_messages'

    _id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(String, nullable=False)
    timestapm = Column(DateTime, default=datetime.now)
    doctor_id = Column(Integer, ForeignKey('doctors._id', ondelete='CASCADE'))
    doctors = relationship('Doctors', back_populates='chat_messages')


