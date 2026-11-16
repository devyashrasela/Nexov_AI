"""Pipecat-callable appointment tools with explicit confirmation guards."""

import asyncio
from datetime import date, time

from config import clinic_now
from db import SessionLocal
from phone import normalize_phone
from store import book_slot, cancel_for_phone, find_doctors, get_free_slots, get_active_appointments_for_phone


def _date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _time(value: str) -> time | None:
    try:
        return time.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _spoken_slot(slot: dict) -> str:
    slot_date = date.fromisoformat(slot["date"])
    slot_time = time.fromisoformat(slot["time"])
    date_text = slot_date.strftime("%A, %B %d").replace(" 0", " ")
    time_text = slot_time.strftime("%I:%M %p").lstrip("0")
    return f"{date_text} at {time_text}"


def _availability_sync(doctor_name: str | None, speciality: str | None, requested_date: str | None) -> dict:
    today = clinic_now().date()
    parsed_date = _date(requested_date) if requested_date else None
    if requested_date and not parsed_date:
        return {"ok": False, "error": "invalid_date", "message": "Please use a valid date."}
    if parsed_date and parsed_date < today:
        return {"ok": False, "error": "date_in_past", "message": "That date has already passed."}
    with SessionLocal() as session:
        doctors = find_doctors(session, doctor_name, speciality)
        if (doctor_name or speciality) and not doctors:
            return {"ok": False, "error": "doctor_not_found", "message": "I could not find that doctor or speciality."}
        doctor_ids = {doctor.id for doctor in doctors} if doctors else None
        slots = []
        for doctor_id in doctor_ids or []:
            slots.extend(get_free_slots(session, doctor_id, parsed_date)[:6])
        if not doctor_ids:
            slots = get_free_slots(session, date_filter=parsed_date)
        grouped: dict[int, dict] = {}
        for slot in slots:
            item = grouped.setdefault(
                slot["doctor_id"],
                {"doctor_id": slot["doctor_id"], "name": slot["doctor_name"], "speciality": slot["speciality"], "slots": []},
            )
            if len(item["slots"]) < 6:
                item["slots"].append({"date": slot["date"], "time": slot["time"]})
        if not grouped:
            return {
                "ok": False,
                "error": "no_slots",
                "message": f"There are no free slots for that request. Today is {today.isoformat()}.",
            }
        spoken_options = []
        for doctor in grouped.values():
            for slot in doctor["slots"]:
                spoken_options.append(
                    f"{doctor['name']} is a {doctor['speciality']} and has an appointment "
                    f"{_spoken_slot(slot)}."
                )
                if len(spoken_options) == 3:
                    break
            if len(spoken_options) == 3:
                break
        return {
            "ok": True,
            "today": today.isoformat(),
            "spoken_summary": " ".join(spoken_options),
            "doctors": list(grouped.values()),
        }


def _book_sync(
    phone_number: str = "",
    phone_confirmed: bool = False,
    doctor_id: int | None = None,
    requested_date: str = "",
    requested_time: str = "",
) -> dict:
    if phone_confirmed is not True:
        return {"ok": False, "error": "phone_not_confirmed", "message": "The phone number must be confirmed first."}
    if not doctor_id or not requested_date or not requested_time:
        return {"ok": False, "error": "missing_slot", "message": "Please select a specific doctor, date, and time first."}
    if not phone_number:
        return {"ok": False, "error": "missing_phone", "message": "Please provide a valid 10-digit mobile number."}
    phone = normalize_phone(phone_number)
    if not phone:
        return {"ok": False, "error": "invalid_phone", "message": "That does not look like a valid 10-digit mobile number."}
    parsed_date = _date(requested_date)
    parsed_time = _time(requested_time)
    if not parsed_date or not parsed_time:
        return {"ok": False, "error": "invalid_slot", "message": "That date or time is invalid."}
    with SessionLocal() as session:
        return book_slot(session, phone, doctor_id, parsed_date, parsed_time)


def _cancel_sync(
    phone_number: str = "",
    phone_confirmed: bool = False,
    appointment_id: int | None = None,
) -> dict:
    if phone_confirmed is not True:
        return {"ok": False, "error": "phone_not_confirmed", "message": "The phone number must be confirmed first."}
    if not phone_number:
        return {"ok": False, "error": "missing_phone", "message": "Please provide a valid 10-digit mobile number."}
    phone = normalize_phone(phone_number)
    if not phone:
        return {"ok": False, "error": "invalid_phone", "message": "That does not look like a valid 10-digit mobile number."}
    with SessionLocal() as session:
        return cancel_for_phone(session, phone, appointment_id)


async def check_doctor_availability(
    doctor_name: str | None = None,
    speciality: str | None = None,
    date: str | None = None,
) -> dict:
    return await asyncio.to_thread(_availability_sync, doctor_name, speciality, date)


async def book_appointment(
    phone_number: str = "",
    phone_confirmed: bool = False,
    doctor_id: int | None = None,
    date: str = "",
    time: str = "",
) -> dict:
    return await asyncio.to_thread(_book_sync, phone_number, phone_confirmed, doctor_id, date, time)


async def cancel_appointment(
    phone_number: str = "",
    phone_confirmed: bool = False,
    appointment_id: int | None = None,
) -> dict:
    return await asyncio.to_thread(_cancel_sync, phone_number, phone_confirmed, appointment_id)
