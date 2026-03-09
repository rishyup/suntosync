from typing import Dict


def classify_readiness(sunlight_minutes: int) -> str:
    if sunlight_minutes < 20:
        return "Low"
    if sunlight_minutes > 30:
        return "High"
    return "Moderate"


def health_score(
    walk_mins: int,
    fatigue: int,
    nap_mins: int,
    sunlight_mins: int,
    activity: str,
    meal_quality: Dict[str, int],
) -> int:
    score = 45
    score += min(walk_mins, 75) // 3

    if sunlight_mins < 20:
        score -= 14
    elif sunlight_mins > 30:
        score += 22
    else:
        score += 10

    score -= max(0, fatigue - 3) * 3

    if 10 <= nap_mins <= 30:
        score += 6
    elif nap_mins > 60:
        score -= 10

    activity_bonus = {"Walking": 4, "Yoga": 7, "Gym": 6}
    score += activity_bonus.get(activity, 3)

    score += min(meal_quality["protein_hits"], 3) * 3
    score += min(meal_quality["fiber_hits"], 3) * 3
    score -= min(meal_quality["refined_hits"], 3) * 3
    score -= min(meal_quality["sugar_hits"], 2) * 4

    return int(max(1, min(100, score)))


def circadian_alignment_score(
    sunlight_mins: int,
    sleep_consistency: int,
    activity: str,
    meal_timing_score: int,
    fatigue: int,
) -> Dict[str, object]:
    sunlight_score = 25 if sunlight_mins > 30 else 18 if sunlight_mins >= 20 else 10
    sleep_score = max(0, min(25, sleep_consistency))
    activity_map = {"Yoga": 20, "Gym": 18, "Walking": 16}
    activity_score = activity_map.get(activity, 14)
    meal_score = max(0, min(15, meal_timing_score))
    fatigue_score = max(0, min(15, 15 - (fatigue - 1) * 1.5))

    total = int(round(sunlight_score + sleep_score + activity_score + meal_score + fatigue_score))
    total = max(1, min(100, total))

    if total >= 80:
        status = "Strong Rhythm"
    elif total >= 65:
        status = "Stable Rhythm"
    elif total >= 50:
        status = "Needs Alignment"
    else:
        status = "Rhythm Disrupted"

    return {
        "alignment_score": total,
        "status": status,
        "factors": {
            "Sunlight": sunlight_score,
            "Sleep Consistency": sleep_score,
            "Activity": activity_score,
            "Meal Timing": meal_score,
            "Fatigue": fatigue_score,
        },
    }
