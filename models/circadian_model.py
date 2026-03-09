from datetime import datetime, timedelta
from typing import Dict


def get_chronotype(wake_pref: str) -> str:
    mapping = {
        "Early Bird": "Morning",
        "Balanced": "Intermediate",
        "Night Owl": "Evening",
    }
    return mapping.get(wake_pref, "Intermediate")


def sleep_phase_calculator(
    sunlight_mins: int,
    activity: str,
    chronotype: str,
    fatigue: int,
) -> Dict[str, str]:
    base_sleep = datetime.strptime("22:45", "%H:%M")

    if chronotype == "Morning":
        base_sleep -= timedelta(minutes=20)
    elif chronotype == "Evening":
        base_sleep += timedelta(minutes=35)

    if sunlight_mins > 30:
        base_sleep -= timedelta(minutes=10)
    elif sunlight_mins < 20:
        base_sleep += timedelta(minutes=15)

    if activity == "Gym":
        base_sleep += timedelta(minutes=10)
    elif activity == "Yoga":
        base_sleep -= timedelta(minutes=10)

    if fatigue >= 7:
        base_sleep -= timedelta(minutes=10)

    wake_time = base_sleep + timedelta(hours=7, minutes=35)

    return {
        "sleep_time": base_sleep.strftime("%I:%M %p"),
        "wake_time": wake_time.strftime("%I:%M %p"),
    }


def circadian_simulation(fatigue: int, sunlight: int, activity: str) -> Dict[str, list]:
    hours = list(range(24))

    cortisol = []
    melatonin = []
    energy = []

    sunlight_boost = 1.1 if sunlight > 30 else 0.9 if sunlight < 20 else 1.0
    activity_boost = 1.08 if activity in ["Gym", "Yoga"] else 1.0
    fatigue_drag = max(0.65, 1.0 - (fatigue - 3) * 0.05)

    for h in hours:
        c = max(0, 90 - abs(8 - h) * 10) * sunlight_boost
        m = max(0, 90 - abs(22 - h) * 12)
        e = max(0, 100 - abs(10 - h) * 9) * sunlight_boost * activity_boost * fatigue_drag

        if 14 <= h <= 16:
            e *= 0.78

        cortisol.append(round(min(100, c), 2))
        melatonin.append(round(min(100, m), 2))
        energy.append(round(min(100, e), 2))

    return {
        "hour": hours,
        "cortisol": cortisol,
        "melatonin": melatonin,
        "energy": energy,
    }
