"""Database models for doctors, availability slots, and appointments."""

from datetime import UTC, date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    speciality: Mapped[str] = mapped_column(String(100), nullable=False)
    slots: Mapped[list["Slot"]] = relationship(back_populates="doctor", cascade="all, delete-orphan")


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (
        UniqueConstraint("doctor_id", "slot_date", "slot_time", name="uq_doctor_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"), nullable=False, index=True)
    slot_date: Mapped[date] = mapped_column(Date, nullable=False)
    slot_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    doctor: Mapped[Doctor] = relationship(back_populates="slots")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="slot")


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (Index("ix_appointments_phone_number", "phone_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(15), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="booked", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    slot: Mapped[Slot] = relationship(back_populates="appointments")
