"""Create deterministic demo doctors and rolling availability slots."""

import argparse
from datetime import time, timedelta

from db import Base, SessionLocal, engine
from config import clinic_now
from models import Doctor, Slot


DOCTORS = [
    ("Dr. Anjali Sharma", "General Physician"),
    ("Dr. Rohan Mehta", "Cardiologist"),
    ("Dr. Kavya Iyer", "Dermatologist"),
    ("Dr. Vikram Singh", "Pediatrician"),
    ("Dr. Neha Kapoor", "Orthopedic"),
]


def seed(reset: bool = False) -> tuple[int, int]:
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        if session.query(Doctor).count():
            return session.query(Doctor).count(), session.query(Slot).count()
        doctors = [Doctor(name=name, speciality=speciality) for name, speciality in DOCTORS]
        session.add_all(doctors)
        session.flush()
        today = clinic_now().date()
        slots: list[Slot] = []
        for doctor_index, doctor in enumerate(doctors):
            for offset in range(1, 8):
                slot_date = today + timedelta(days=offset)
                if slot_date.weekday() == 6:
                    continue
                times = [time(hour, minute) for hour in (10, 11, 12, 16, 17) for minute in (0, 30)]
                for slot_index, slot_time in enumerate(times):
                    slots.append(
                        Slot(
                            doctor_id=doctor.id,
                            slot_date=slot_date,
                            slot_time=slot_time,
                            is_booked=(doctor_index + slot_index + offset) % 11 == 0,
                        )
                    )
        session.add_all(slots)
        session.commit()
        return len(doctors), len(slots)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    doctor_count, slot_count = seed(args.reset)
    print(f"Created {doctor_count} doctors, {slot_count} slots.")
