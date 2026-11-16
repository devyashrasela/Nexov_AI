"""The only module that talks to SQLAlchemy models."""

from datetime import UTC, date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from models import Appointment, Doctor, Slot


def _slot_dict(slot: Slot) -> dict:
    return {
        "id": slot.id,
        "date": slot.slot_date.isoformat(),
        "time": slot.slot_time.strftime("%H:%M"),
        "is_booked": slot.is_booked,
    }


def _doctor_dict(doctor: Doctor, slots: list[Slot] | None = None) -> dict:
    return {
        "id": doctor.id,
        "name": doctor.name,
        "speciality": doctor.speciality,
        "slots": [_slot_dict(slot) for slot in (slots if slots is not None else doctor.slots)],
    }


def get_doctors_with_slots(session: Session, date_filter: date | None = None, only_free: bool = False) -> list[dict]:
    doctors = session.scalars(select(Doctor).order_by(Doctor.name)).all()
    result = []
    for doctor in doctors:
        slots = sorted(doctor.slots, key=lambda item: (item.slot_date, item.slot_time))
        if date_filter:
            slots = [slot for slot in slots if slot.slot_date == date_filter]
        if only_free:
            slots = [slot for slot in slots if not slot.is_booked]
        result.append(_doctor_dict(doctor, slots))
    return result


def find_doctors(session: Session, name: str | None = None, speciality: str | None = None) -> list[Doctor]:
    query = select(Doctor).order_by(Doctor.name)
    if name:
        query = query.where(Doctor.name.ilike(f"%{name}%"))
    if speciality:
        query = query.where(Doctor.speciality.ilike(f"%{speciality}%"))
    return list(session.scalars(query).all())


def get_free_slots(session: Session, doctor_id: int | None = None, date_filter: date | None = None) -> list[dict]:
    query = select(Slot).options(joinedload(Slot.doctor)).where(Slot.is_booked.is_(False))
    if doctor_id:
        query = query.where(Slot.doctor_id == doctor_id)
    if date_filter:
        query = query.where(Slot.slot_date == date_filter)
    slots = session.scalars(query.order_by(Slot.slot_date, Slot.slot_time)).all()
    return [
        {
            "id": slot.id,
            "doctor_id": slot.doctor_id,
            "doctor_name": slot.doctor.name,
            "speciality": slot.doctor.speciality,
            "date": slot.slot_date.isoformat(),
            "time": slot.slot_time.strftime("%H:%M"),
        }
        for slot in slots
    ]


def book_slot(session: Session, phone: str, doctor_id: int, slot_date: date, slot_time: time) -> dict:
    slot = session.scalar(
        select(Slot).where(
            Slot.doctor_id == doctor_id,
            Slot.slot_date == slot_date,
            Slot.slot_time == slot_time,
        )
    )
    if not slot:
        return {"ok": False, "error": "slot_not_found", "message": "That appointment slot does not exist."}
    if slot.is_booked:
        alternatives = get_free_slots(session, doctor_id, slot_date)[:3]
        return {"ok": False, "error": "slot_taken", "message": "That slot is already booked.", "alternatives": alternatives}
    duplicate = session.scalar(
        select(Appointment)
        .join(Appointment.slot)
        .where(
            Appointment.phone_number == phone,
            Appointment.status == "booked",
            Slot.doctor_id == doctor_id,
            Slot.slot_date == slot_date,
        )
    )
    if duplicate:
        return {"ok": False, "error": "duplicate_appointment", "message": "This caller already has an appointment with that doctor on that day."}
    slot.is_booked = True
    appointment = Appointment(slot=slot, phone_number=phone, status="booked")
    session.add(appointment)
    session.commit()
    session.refresh(appointment)
    return {
        "ok": True,
        "appointment": {
            "id": appointment.id,
            "phone_number": phone,
            "doctor_id": slot.doctor_id,
            "doctor_name": slot.doctor.name,
            "speciality": slot.doctor.speciality,
            "date": slot.slot_date.isoformat(),
            "time": slot.slot_time.strftime("%H:%M"),
            "status": appointment.status,
        },
    }


def get_active_appointments_for_phone(session: Session, phone: str) -> list[dict]:
    appointments = session.scalars(
        select(Appointment)
        .options(joinedload(Appointment.slot).joinedload(Slot.doctor))
        .where(Appointment.phone_number == phone, Appointment.status == "booked")
        .order_by(Appointment.created_at.desc())
    ).all()
    return [_appointment_dict(appointment) for appointment in appointments]


def cancel_for_phone(session: Session, phone: str, appointment_id: int | None = None) -> dict:
    appointments = session.scalars(
        select(Appointment)
        .options(joinedload(Appointment.slot).joinedload(Slot.doctor))
        .where(Appointment.phone_number == phone, Appointment.status == "booked")
    ).all()
    if not appointments:
        return {"ok": False, "error": "no_appointment", "message": "No active appointment was found for that phone number."}
    if appointment_id is not None:
        appointments = [appointment for appointment in appointments if appointment.id == appointment_id]
        if not appointments:
            return {"ok": False, "error": "appointment_not_found", "message": "That appointment was not found for this phone number."}
    elif len(appointments) > 1:
        return {"ok": False, "error": "multiple_appointments", "message": "There is more than one active appointment.", "appointments": [_appointment_dict(item) for item in appointments]}
    appointment = appointments[0]
    appointment.status = "cancelled"
    appointment.cancelled_at = datetime.now(UTC).replace(tzinfo=None)
    appointment.slot.is_booked = False
    session.commit()
    return {"ok": True, "appointment": _appointment_dict(appointment)}


def _appointment_dict(appointment: Appointment) -> dict:
    slot = appointment.slot
    return {
        "id": appointment.id,
        "phone_number": appointment.phone_number,
        "doctor": {
            "id": slot.doctor.id,
            "name": slot.doctor.name,
            "speciality": slot.doctor.speciality,
        },
        "date": slot.slot_date.isoformat(),
        "time": slot.slot_time.strftime("%H:%M"),
        "status": appointment.status,
        "created_at": appointment.created_at.isoformat(),
        "cancelled_at": appointment.cancelled_at.isoformat() if appointment.cancelled_at else None,
    }


def list_appointments(session: Session, status: str | None = None) -> list[dict]:
    query = (
        select(Appointment)
        .options(joinedload(Appointment.slot).joinedload(Slot.doctor))
        .order_by(Appointment.created_at.desc())
    )
    if status:
        query = query.where(Appointment.status == status)
    return [_appointment_dict(appointment) for appointment in session.scalars(query).all()]
