from typing import Dict, List


def coach_insight_engine(history_len: int, latest: Dict, corr_val: float) -> List[str]:
    insights: List[str] = []

    sunlight = int(latest.get("sunlight", 0))
    fatigue = int(latest.get("fatigue", 5))
    alignment = float(latest.get("alignment_score", 0))

    if history_len >= 7 and sunlight < 20:
        insights.append("Your morning sunlight trend is low this week. This can delay melatonin onset.")

    if corr_val <= -0.35:
        insights.append("Your data shows a strong inverse sunlight-fatigue trend. More sunlight likely lowers fatigue.")

    if fatigue >= 7:
        insights.append("Fatigue is elevated. Try a lighter dinner and fixed wind-down routine tonight.")

    if alignment >= 80:
        insights.append("Circadian alignment is strong. Maintain wake-time consistency to preserve gains.")

    if not insights:
        insights.append("Signal pattern is stable. Keep your current rhythm protocol for 3 days.")

    return insights[:4]


def daily_report_card(
    sunlight_debt: int,
    orbit: str,
    chronotype_signal: str,
    top_reco: str,
    next_action: str,
) -> str:
    return (
        "Daily Rhythm Report\n\n"
        f"Sunlight Debt: {sunlight_debt} min\n"
        f"Metabolic Orbit: {orbit}\n"
        f"Chronotype Signal: {chronotype_signal}\n\n"
        f"Top Recommendation: {top_reco}\n"
        f"Next Action: {next_action}"
    )
