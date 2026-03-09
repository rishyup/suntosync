from datetime import datetime

import streamlit as st

from analytics.trend_analysis import (
    activity_impact,
    as_dataframe,
    circadian_gauge,
    factor_weight_chart,
    meal_impact_heatmap,
    nap_vs_productivity,
    sunlight_fatigue_corr,
    trend_30_day,
)
from database.db_manager import DBManager
from models.coach_engine import coach_insight_engine, daily_report_card
from models.circadian_model import circadian_simulation, get_chronotype, sleep_phase_calculator
from models.wearable_fusion import (
    baseline_sleep_hours,
    build_wearable_daily_features,
    get_wearable_context,
    list_ids_dates,
    load_all_datasets,
    suggest_activity_from_wearable,
    wearable_enhancement,
)
from recommendations.meal_engine import build_nutrition_table, meal_quality_signals, personalized_dinner_plan
from reports.report_generator import build_weekly_pdf_report
from utils.auth import hash_password, verify_password
from utils.scoring import circadian_alignment_score, classify_readiness, health_score

st.set_page_config(page_title="Circadian Health Platform", page_icon="CM", layout="wide")

THEMES = {
    "Sunrise Mint": {
        "bg": "linear-gradient(145deg, #fffefb 0%, #eff7f4 100%)",
        "hero": "linear-gradient(120deg, rgba(229, 106, 10, 0.20), rgba(8, 127, 91, 0.20))",
        "hero_border": "rgba(8, 127, 91, 0.55)",
        "ink": "#0f1c2c",
    },
    "Ocean Light": {
        "bg": "linear-gradient(145deg, #f9fcff 0%, #ecf4ff 100%)",
        "hero": "linear-gradient(120deg, rgba(31, 117, 254, 0.18), rgba(0, 170, 160, 0.18))",
        "hero_border": "rgba(31, 117, 254, 0.45)",
        "ink": "#10243a",
    },
    "Earth Sand": {
        "bg": "linear-gradient(145deg, #fffaf0 0%, #f6f1e7 100%)",
        "hero": "linear-gradient(120deg, rgba(167, 111, 67, 0.22), rgba(94, 138, 111, 0.18))",
        "hero_border": "rgba(167, 111, 67, 0.45)",
        "ink": "#1e2a23",
    },
}

CALORIE_BRACKETS = ["0-100", "100-200", "200-300", "300+"]


def bracket_midpoint(label: str) -> int:
    return {"0-100": 50, "100-200": 150, "200-300": 250}.get(label, 350)


def meal_intake_feedback(total_intake: int) -> str:
    if total_intake < 250:
        return "Daytime intake is light. Dinner can be moderately higher in calories and protein."
    if total_intake < 450:
        return "Daytime intake is moderate. Keep dinner balanced."
    if total_intake < 650:
        return "Daytime intake is already substantial. Prefer lighter, fiber-rich dinner."
    return "Daytime intake is high. Keep dinner low-carb, high-protein, and early."


def health_risk_flags(fatigue: int, stress: int, hydration_glasses: int, sunlight: int, nap_mins: int, sleep_consistency: int) -> list[str]:
    flags: list[str] = []
    if fatigue >= 7:
        flags.append("High fatigue load")
    if stress >= 7:
        flags.append("High stress signal")
    if hydration_glasses < 6:
        flags.append("Low hydration")
    if sunlight < 20:
        flags.append("Insufficient morning light")
    if nap_mins > 60:
        flags.append("Long daytime nap")
    if sleep_consistency < 14:
        flags.append("Poor sleep consistency")
    return flags


def recovery_actions(stress: int, hydration_glasses: int, sunlight: int, fatigue: int) -> list[str]:
    actions: list[str] = []
    if sunlight < 20:
        actions.append("Get 20-30 minutes sunlight in the first hour after waking.")
    if hydration_glasses < 6:
        actions.append("Add 2-3 glasses of water before evening.")
    if stress >= 7:
        actions.append("Do 8-10 minutes slow breathing before sleep.")
    if fatigue >= 7:
        actions.append("Keep dinner light and finish 2-3 hours before bed.")
    if not actions:
        actions.append("Maintain this routine tomorrow to reinforce circadian stability.")
    return actions[:4]


def wellness_score(alignment_score: int, fatigue: int, stress: int, hydration_glasses: int) -> int:
    score = alignment_score
    score -= max(0, fatigue - 4) * 4
    score -= max(0, stress - 4) * 3
    score += min(10, hydration_glasses)
    return max(1, min(100, int(score)))


def inject_theme(theme_name: str, high_contrast: bool = False) -> None:
    t = THEMES.get(theme_name, THEMES["Sunrise Mint"])
    ink = "#06111d" if high_contrast else t["ink"]
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {t['bg']}; color: {ink}; }}
        .stApp * {{ color: {ink} !important; }}
        .hero {{ padding: 1rem 1.3rem; border-radius: 20px; background: {t['hero']}; border: 1px solid {t['hero_border']}; }}
        .glass-card {{ border-radius: 16px; border: 1px solid rgba(15,28,44,0.16); background: #fff; box-shadow: 0 8px 20px rgba(0,0,0,0.07); padding: 0.8rem 1rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def cached_nutrition_table():
    return build_nutrition_table()


@st.cache_data(show_spinner=False)
def cached_wearable_data():
    raw_data, source_map = load_all_datasets()
    fused = build_wearable_daily_features(raw_data)
    baseline_sleep = baseline_sleep_hours(raw_data)
    return source_map, fused, baseline_sleep


def init_state() -> None:
    if "user" not in st.session_state:
        st.session_state.user = None


def auth_panel(db: DBManager) -> None:
    st.sidebar.subheader("Account")
    mode = st.sidebar.radio("Access", ["Login", "Signup"], horizontal=True)
    username = st.sidebar.text_input("Username", key="auth_user")
    password = st.sidebar.text_input("Password", type="password", key="auth_pass")

    if mode == "Signup" and st.sidebar.button("Create Account"):
        if username and password:
            ok = db.create_user(username, hash_password(password), datetime.now().isoformat())
            st.sidebar.success("Account created. Login now." if ok else "Username already exists")
        else:
            st.sidebar.error("Enter username and password")

    if mode == "Login" and st.sidebar.button("Login"):
        user = db.get_user(username)
        if user and verify_password(password, user["password_hash"]):
            st.session_state.user = user
            st.sidebar.success(f"Logged in: {username}")
        else:
            st.sidebar.error("Invalid credentials")

    if st.session_state.user:
        st.sidebar.info(f"Active User: {st.session_state.user['username']}")
        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.rerun()


def main() -> None:
    init_state()
    st.sidebar.subheader("Appearance")
    theme_name = st.sidebar.selectbox("Theme", list(THEMES.keys()), index=0)
    high_contrast = st.sidebar.toggle("High Contrast Text", value=True)
    inject_theme(theme_name, high_contrast)

    db = DBManager()
    nutrition_df, nutrition_sources = cached_nutrition_table()
    wearable_sources, wearable_daily, baseline_sleep = cached_wearable_data()

    auth_panel(db)

    st.markdown("<div class='hero'><h1>Circadian Health Platform</h1><p>Health-first rhythm tracking with sleep, stress, hydration, recovery, and optional food support.</p></div>", unsafe_allow_html=True)

    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.write("**Data Sources**")
    st.write(f"Nutrition files loaded: {sum(1 for v in nutrition_sources.values() if v is not None)}/{len(nutrition_sources)}")
    st.write(f"Wearable files loaded: {sum(1 for v in wearable_sources.values() if v is not None)}/{len(wearable_sources)}")
    st.markdown("</div>", unsafe_allow_html=True)

    ids, dates_by_id = list_ids_dates(wearable_daily)
    st.sidebar.subheader("Wearable Fusion")
    use_wearable = st.sidebar.checkbox("Use wearable context in model", value=bool(ids))
    selected_id = st.sidebar.selectbox("Wearable Participant Id", ids) if ids else None
    selected_date = None
    wearable_context = {}
    enhancement = {}
    if selected_id:
        selected_dates = dates_by_id.get(selected_id, [])
        if selected_dates:
            selected_date = st.sidebar.selectbox("Wearable Log Date", selected_dates)
            wearable_context = get_wearable_context(wearable_daily, selected_id, selected_date)
            enhancement = wearable_enhancement(wearable_context, baseline_sleep)

    if not st.session_state.user:
        st.warning("Login or signup to save data and access personalized dashboards.")
        return

    st.subheader("Daily Health Inputs")
    with st.form("daily_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            diet_pref = st.radio("Diet", ["Vegetarian", "Non-Vegetarian"], horizontal=True)
            walk_duration = st.number_input("Morning walk (min)", min_value=0, max_value=300, value=30, step=5)
        with c2:
            activity = st.selectbox("Activity", ["Walking", "Yoga", "Gym"])
            fatigue = st.slider("Fatigue", 1, 10, 5)
        with c3:
            nap_duration = st.number_input("Nap (min)", min_value=0, max_value=240, value=20, step=5)
            sunlight = st.number_input("Sunlight (min)", min_value=0, max_value=180, value=20, step=5)
        with c4:
            chronotype_pref = st.selectbox("Chronotype Preference", ["Early Bird", "Balanced", "Night Owl"])
            sleep_consistency = st.slider("Sleep Consistency", 0, 25, 18)

        stress = st.slider("Stress Level", 1, 10, 5)
        hydration_glasses = st.slider("Water Intake (glasses)", 0, 16, 7)

        breakfast = st.text_input("Breakfast")
        breakfast_cal = st.selectbox("Breakfast Calories", CALORIE_BRACKETS)
        lunch = st.text_input("Lunch")
        lunch_cal = st.selectbox("Lunch Calories", CALORIE_BRACKETS)
        meal_timing_score = st.slider("Meal Timing Score", 0, 15, 10)

        submitted = st.form_submit_button("Analyze Health")

    if submitted:
        eff_activity = activity
        eff_sunlight = int(sunlight)
        eff_fatigue = int(fatigue)
        cal_adjust = 0.0
        prot_adjust = 0.0

        if use_wearable and wearable_context:
            eff_activity = suggest_activity_from_wearable(wearable_context)
            eff_sunlight = int(max(eff_sunlight, enhancement.get("sunlight_proxy", 0)))
            eff_fatigue = int(max(1, min(10, round(eff_fatigue + enhancement.get("fatigue_adjust", 0)))))
            cal_adjust += enhancement.get("calorie_boost", 0.0)
            prot_adjust += enhancement.get("protein_boost", 0.0)

        daytime_intake = bracket_midpoint(breakfast_cal) + bracket_midpoint(lunch_cal)
        if daytime_intake < 250:
            cal_adjust += 140
            prot_adjust += 3
        elif daytime_intake > 650:
            cal_adjust -= 120
            prot_adjust += 2

        meal_signals = meal_quality_signals(breakfast, lunch)
        h_score = health_score(int(walk_duration), eff_fatigue, int(nap_duration), eff_sunlight, eff_activity, meal_signals)

        align = circadian_alignment_score(
            sunlight_mins=eff_sunlight,
            sleep_consistency=int(sleep_consistency),
            activity=eff_activity,
            meal_timing_score=int(meal_timing_score),
            fatigue=eff_fatigue,
        )

        w_score = wellness_score(align["alignment_score"], eff_fatigue, int(stress), int(hydration_glasses))
        flags = health_risk_flags(eff_fatigue, int(stress), int(hydration_glasses), eff_sunlight, int(nap_duration), int(sleep_consistency))
        actions = recovery_actions(int(stress), int(hydration_glasses), eff_sunlight, eff_fatigue)

        dinner_plan = personalized_dinner_plan(
            nutrition_df=nutrition_df,
            diet_pref=diet_pref,
            fatigue=eff_fatigue,
            activity=eff_activity,
            health_score_value=h_score,
            calorie_adjust=cal_adjust,
            protein_adjust=prot_adjust,
        )

        chrono = get_chronotype(chronotype_pref)
        sleep_plan = sleep_phase_calculator(eff_sunlight, eff_activity, chrono, eff_fatigue)

        now = datetime.now()
        daily = {
            "log_date": now.strftime("%Y-%m-%d"),
            "diet_pref": diet_pref,
            "walk_duration": int(walk_duration),
            "activity": eff_activity,
            "fatigue": eff_fatigue,
            "nap_duration": int(nap_duration),
            "sunlight": eff_sunlight,
            "breakfast": breakfast,
            "lunch": lunch,
            "created_at": now.isoformat(),
        }

        db.save_daily_bundle(
            user_id=st.session_state.user["id"],
            daily=daily,
            dinner={"meal_name": dinner_plan["meal_name"], "calories": dinner_plan["calories"], "protein": dinner_plan["protein"]},
            sleep={"sleep_time": sleep_plan["sleep_time"], "wake_time": sleep_plan["wake_time"], "chronotype": chrono},
            score={"health_score": h_score, "alignment_score": align["alignment_score"], "status": align["status"]},
        )

        st.success("Health analysis saved.")

        st.subheader("Health Command Center")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Wellness Score", f"{w_score}/100")
        k2.metric("Alignment", f"{align['alignment_score']}/100")
        k3.metric("Fatigue", f"{eff_fatigue}/10")
        k4.metric("Stress", f"{stress}/10")

        st.write(f"Sleep Window: **{sleep_plan['sleep_time']} - {sleep_plan['wake_time']}**")
        st.write(f"Hydration: **{hydration_glasses} glasses** | Readiness: **{classify_readiness(eff_sunlight)}**")

        st.plotly_chart(circadian_gauge(w_score, "Overall Wellness Gauge"), use_container_width=True)
        st.altair_chart(factor_weight_chart(align["factors"]), use_container_width=True)

        st.subheader("Risk Flags")
        if flags:
            for f in flags:
                st.write(f"- {f}")
        else:
            st.write("- No major risk flags today.")

        st.subheader("Recovery Plan")
        for a in actions:
            st.write(f"- {a}")

        st.info(f"Daytime intake estimate: {daytime_intake} kcal. {meal_intake_feedback(daytime_intake)}")

        with st.expander("Meal Support (Secondary)"):
            st.write("Recommended Dinner")
            for item in dinner_plan["items"]:
                st.write(f"- {item}")
            st.write(f"Protein: **{dinner_plan['protein']} g** | Calories: **{dinner_plan['calories']} kcal**")

        sim = circadian_simulation(eff_fatigue, eff_sunlight, eff_activity)
        st.subheader("Circadian Simulation")
        st.line_chart({"hour": sim["hour"], "energy": sim["energy"], "cortisol": sim["cortisol"], "melatonin": sim["melatonin"]}, x="hour")

        report_text = daily_report_card(
            sunlight_debt=max(0, 30 - eff_sunlight),
            orbit="Rhythm Rise" if align["alignment_score"] >= 70 else "Recovery Dock",
            chronotype_signal="Sun-Synced" if eff_sunlight >= 30 and eff_fatigue <= 4 else "Adaptive",
            top_reco="Prioritize sleep + hydration + morning light",
            next_action=actions[0],
        )
        st.text(report_text)

    with st.expander("Optional: Food Calorie Finder"):
        search_q = st.text_input("Search food from dataset", placeholder="e.g., paneer, dal, roti, chicken")
        food_df = nutrition_df.copy()
        food_df["dish"] = food_df["dish"].astype(str).str.strip()
        filtered_food = food_df[food_df["dish"].str.contains(search_q, case=False, na=False)].copy() if search_q else food_df.head(50).copy()
        if filtered_food.empty:
            st.warning("No food found for this search.")
        else:
            options = filtered_food["dish"].dropna().unique().tolist()
            selected_food = st.selectbox("Select food", options)
            selected_row = filtered_food[filtered_food["dish"] == selected_food].head(1)
            if not selected_row.empty:
                cal_val = float(selected_row["calories"].iloc[0]) if "calories" in selected_row.columns else 0.0
                prot_val = float(selected_row["protein"].iloc[0]) if "protein" in selected_row.columns else 0.0
                c1, c2 = st.columns(2)
                c1.metric("Calories", f"{cal_val:.1f} kcal")
                c2.metric("Protein", f"{prot_val:.1f} g")

    rows = db.get_user_history(st.session_state.user["id"], days=90)
    df = as_dataframe(rows)
    if df.empty:
        return

    st.subheader("Health Analytics")
    tab1, tab2, tab3 = st.tabs(["Trends", "Correlations", "Impact"])
    with tab1:
        fig = trend_30_day(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    with tab2:
        corr_fig, corr_val = sunlight_fatigue_corr(df)
        if corr_fig:
            st.plotly_chart(corr_fig, use_container_width=True)
            st.write(f"Sunlight vs Fatigue Correlation: **{corr_val:.2f}**")
        heat = meal_impact_heatmap(df)
        if heat:
            st.pyplot(heat)
    with tab3:
        act_fig = activity_impact(df)
        nap_fig = nap_vs_productivity(df)
        if act_fig:
            st.plotly_chart(act_fig, use_container_width=True)
        if nap_fig:
            st.plotly_chart(nap_fig, use_container_width=True)
        corr_val = float(df[["sunlight", "fatigue"]].corr().iloc[0, 1]) if len(df) > 1 else 0.0
        latest = df.tail(1).to_dict(orient="records")[0]
        for i in coach_insight_engine(len(df), latest, corr_val):
            st.write(f"- {i}")

    weekly = df.tail(7)
    if not weekly.empty:
        metrics = {
            "Avg Health Score": f"{weekly['health_score'].mean():.1f}",
            "Avg Alignment Score": f"{weekly['alignment_score'].mean():.1f}",
            "Avg Sunlight": f"{weekly['sunlight'].mean():.1f} min",
            "Avg Fatigue": f"{weekly['fatigue'].mean():.1f}",
        }
        summary = {
            "Best Activity": str(weekly.groupby("activity")["alignment_score"].mean().idxmax()),
            "Most Common Status": str(weekly["status"].mode().iloc[0]) if not weekly["status"].mode().empty else "N/A",
            "Sunlight-Fatigue Correlation": f"{(weekly[['sunlight', 'fatigue']].corr().iloc[0, 1] if len(weekly)>1 else 0.0):.2f}",
        }
        pdf_bytes = build_weekly_pdf_report(st.session_state.user["username"], metrics, summary)
        st.download_button("Download Weekly Health Report (PDF)", data=pdf_bytes, file_name=f"weekly_report_{st.session_state.user['username']}.pdf", mime="application/pdf")


if __name__ == "__main__":
    main()
