from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DOWNLOADS = Path(r"C:\Users\PC\Downloads\archive (1)")

DATASET_FILES = [
    "minuteMETsNarrow_merged.csv",
    "minuteSleep_merged.csv",
    "minuteStepsNarrow_merged.csv",
    "minuteStepsWide_merged.csv",
    "sleepDay_merged.csv",
    "weightLogInfo_merged.csv",
    "dailyActivity_merged.csv",
    "dailyCalories_merged.csv",
    "dailyIntensities_merged.csv",
    "dailySteps_merged.csv",
    "heartrate_seconds_merged.csv",
    "hourlyCalories_merged.csv",
    "hourlyIntensities_merged.csv",
    "hourlySteps_merged.csv",
    "minuteCaloriesNarrow_merged.csv",
    "minuteCaloriesWide_merged.csv",
    "minuteIntensitiesNarrow_merged.csv",
    "minuteIntensitiesWide_merged.csv",
    "Sleep Health and Lifestyle Dataset.xlsx",
]

READ_HINTS = {
    "minuteMETsNarrow_merged.csv": {"usecols": ["Id", "ActivityMinute", "METs"], "nrows": 300000},
    "minuteSleep_merged.csv": {"usecols": ["Id", "date", "value", "logId"], "nrows": 300000},
    "minuteStepsNarrow_merged.csv": {"usecols": ["Id", "ActivityMinute", "Steps"], "nrows": 300000},
    "minuteStepsWide_merged.csv": {"nrows": 10000},
    "sleepDay_merged.csv": {"usecols": ["Id", "SleepDay", "TotalSleepRecords", "TotalMinutesAsleep", "TotalTimeInBed"]},
    "weightLogInfo_merged.csv": {"usecols": ["Id", "Date", "WeightKg", "WeightPounds", "BMI"]},
    "dailyActivity_merged.csv": {"usecols": ["Id", "ActivityDate", "TotalSteps", "Calories", "VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes", "SedentaryMinutes"]},
    "dailyCalories_merged.csv": {"usecols": ["Id", "ActivityDay", "Calories"]},
    "dailyIntensities_merged.csv": {"usecols": ["Id", "ActivityDay", "VeryActiveMinutes", "FairlyActiveMinutes", "LightlyActiveMinutes", "SedentaryMinutes"]},
    "dailySteps_merged.csv": {"usecols": ["Id", "ActivityDay", "StepTotal"]},
    "heartrate_seconds_merged.csv": {"usecols": ["Id", "Time", "Value"], "nrows": 400000},
    "hourlyCalories_merged.csv": {"usecols": ["Id", "ActivityHour", "Calories"]},
    "hourlyIntensities_merged.csv": {"usecols": ["Id", "ActivityHour", "TotalIntensity", "AverageIntensity"]},
    "hourlySteps_merged.csv": {"usecols": ["Id", "ActivityHour", "StepTotal"]},
    "minuteCaloriesNarrow_merged.csv": {"usecols": ["Id", "ActivityMinute", "Calories"], "nrows": 300000},
    "minuteCaloriesWide_merged.csv": {"nrows": 10000},
    "minuteIntensitiesNarrow_merged.csv": {"usecols": ["Id", "ActivityMinute", "Intensity"], "nrows": 300000},
    "minuteIntensitiesWide_merged.csv": {"nrows": 10000},
}


def _paths_for(filename: str) -> List[Path]:
    return [DOWNLOADS / filename, ROOT / filename]


def _read_file(path: Path, filename: str) -> Optional[pd.DataFrame]:
    try:
        if path.suffix.lower() == ".xlsx":
            return pd.read_excel(path)

        hints = READ_HINTS.get(filename, {})
        kwargs = {"low_memory": False}
        if "usecols" in hints:
            kwargs["usecols"] = hints["usecols"]
        if "nrows" in hints:
            kwargs["nrows"] = hints["nrows"]

        try:
            return pd.read_csv(path, **kwargs)
        except ValueError:
            return pd.read_csv(path, low_memory=False, nrows=hints.get("nrows"))
    except Exception:
        return None


def load_all_datasets() -> Tuple[Dict[str, Optional[pd.DataFrame]], Dict[str, Optional[Path]]]:
    data: Dict[str, Optional[pd.DataFrame]] = {}
    sources: Dict[str, Optional[Path]] = {}

    for fname in DATASET_FILES:
        chosen: Optional[Path] = None
        df: Optional[pd.DataFrame] = None
        for p in _paths_for(fname):
            if p.exists():
                tmp = _read_file(p, fname)
                if tmp is not None:
                    chosen = p
                    df = tmp
                    break
        data[fname] = df
        sources[fname] = chosen

    return data, sources


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    return out


def _pick_col(cols: List[str], options: List[str]) -> Optional[str]:
    low_map = {c.lower(): c for c in cols}
    for o in options:
        if o.lower() in low_map:
            return low_map[o.lower()]
    return None


def _to_day(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.slice(0, 10)
    dt = pd.to_datetime(s, format="%m/%d/%Y", errors="coerce")
    unresolved = dt.isna()
    if unresolved.any():
        dt.loc[unresolved] = pd.to_datetime(s.loc[unresolved], format="%Y-%m-%d", errors="coerce")
    unresolved = dt.isna()
    if unresolved.any():
        dt.loc[unresolved] = pd.to_datetime(s.loc[unresolved], format="%m-%d-%Y", errors="coerce")
    return dt.dt.date.astype("string")


def _extract_daily_metric(
    df: Optional[pd.DataFrame],
    value_options: List[str],
    date_options: List[str],
    agg: str,
    metric_name: str,
) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Id", "log_date", metric_name])

    d = _normalize(df)
    cols = list(d.columns)
    id_col = _pick_col(cols, ["Id", "id"])
    dt_col = _pick_col(cols, date_options)
    val_col = _pick_col(cols, value_options)

    if not id_col or not dt_col or not val_col:
        return pd.DataFrame(columns=["Id", "log_date", metric_name])

    tmp = d[[id_col, dt_col, val_col]].copy()
    tmp["Id"] = pd.to_numeric(tmp[id_col], errors="coerce")
    tmp["log_date"] = _to_day(tmp[dt_col])
    tmp[metric_name] = pd.to_numeric(tmp[val_col], errors="coerce")
    tmp = tmp.dropna(subset=["Id", "log_date", metric_name])

    if tmp.empty:
        return pd.DataFrame(columns=["Id", "log_date", metric_name])

    if agg == "mean":
        out = tmp.groupby(["Id", "log_date"], as_index=False)[metric_name].mean()
    elif agg == "max":
        out = tmp.groupby(["Id", "log_date"], as_index=False)[metric_name].max()
    else:
        out = tmp.groupby(["Id", "log_date"], as_index=False)[metric_name].sum()
    return out


def build_wearable_daily_features(all_data: Dict[str, Optional[pd.DataFrame]]) -> pd.DataFrame:
    parts: List[pd.DataFrame] = []

    parts.append(_extract_daily_metric(all_data.get("dailySteps_merged.csv"), ["StepTotal", "Steps", "TotalSteps"], ["ActivityDay", "ActivityDate", "Date"], "sum", "steps_total"))
    parts.append(_extract_daily_metric(all_data.get("dailyCalories_merged.csv"), ["Calories"], ["ActivityDay", "ActivityDate", "Date"], "sum", "calories_burned"))
    parts.append(_extract_daily_metric(all_data.get("dailyIntensities_merged.csv"), ["VeryActiveMinutes"], ["ActivityDay", "ActivityDate", "Date"], "sum", "very_active_mins"))
    parts.append(_extract_daily_metric(all_data.get("dailyIntensities_merged.csv"), ["FairlyActiveMinutes"], ["ActivityDay", "ActivityDate", "Date"], "sum", "fairly_active_mins"))
    parts.append(_extract_daily_metric(all_data.get("dailyIntensities_merged.csv"), ["LightlyActiveMinutes"], ["ActivityDay", "ActivityDate", "Date"], "sum", "light_active_mins"))

    parts.append(_extract_daily_metric(all_data.get("sleepDay_merged.csv"), ["TotalMinutesAsleep"], ["SleepDay", "Date"], "mean", "sleep_mins"))
    parts.append(_extract_daily_metric(all_data.get("sleepDay_merged.csv"), ["TotalTimeInBed"], ["SleepDay", "Date"], "mean", "time_in_bed_mins"))
    parts.append(_extract_daily_metric(all_data.get("minuteSleep_merged.csv"), ["value", "Value"], ["date", "Date", "Time"], "mean", "minute_sleep_value"))

    parts.append(_extract_daily_metric(all_data.get("heartrate_seconds_merged.csv"), ["Value", "HeartRate"], ["Time", "Date"], "mean", "avg_heart_rate"))
    parts.append(_extract_daily_metric(all_data.get("minuteMETsNarrow_merged.csv"), ["METs", "Mets"], ["ActivityMinute", "Date", "Time"], "mean", "avg_mets"))

    parts.append(_extract_daily_metric(all_data.get("hourlySteps_merged.csv"), ["StepTotal"], ["ActivityHour", "Date", "Time"], "sum", "hourly_steps_sum"))
    parts.append(_extract_daily_metric(all_data.get("hourlyCalories_merged.csv"), ["Calories"], ["ActivityHour", "Date", "Time"], "sum", "hourly_calories_sum"))
    parts.append(_extract_daily_metric(all_data.get("hourlyIntensities_merged.csv"), ["TotalIntensity", "AverageIntensity"], ["ActivityHour", "Date", "Time"], "mean", "hourly_intensity_mean"))
    parts.append(_extract_daily_metric(all_data.get("minuteStepsNarrow_merged.csv"), ["Steps", "StepTotal"], ["ActivityMinute", "Date", "Time"], "sum", "minute_steps_sum"))
    parts.append(_extract_daily_metric(all_data.get("minuteCaloriesNarrow_merged.csv"), ["Calories"], ["ActivityMinute", "Date", "Time"], "sum", "minute_calories_sum"))
    parts.append(_extract_daily_metric(all_data.get("minuteIntensitiesNarrow_merged.csv"), ["Intensity"], ["ActivityMinute", "Date", "Time"], "mean", "minute_intensity_mean"))

    parts.append(_extract_daily_metric(all_data.get("weightLogInfo_merged.csv"), ["WeightKg", "WeightPounds"], ["Date"], "mean", "weight_value"))

    merged: Optional[pd.DataFrame] = None
    for p in parts:
        if p.empty:
            continue
        merged = p.copy() if merged is None else merged.merge(p, on=["Id", "log_date"], how="outer")

    if merged is None:
        return pd.DataFrame(columns=["Id", "log_date"])

    return merged.sort_values(["Id", "log_date"]).reset_index(drop=True)


def baseline_sleep_hours(all_data: Dict[str, Optional[pd.DataFrame]]) -> float:
    df = all_data.get("Sleep Health and Lifestyle Dataset.xlsx")
    if df is None or df.empty:
        return 7.2

    d = _normalize(df)
    col = _pick_col(list(d.columns), ["Sleep Duration", "sleep duration"])
    if not col:
        return 7.2

    vals = pd.to_numeric(d[col], errors="coerce").dropna()
    return float(vals.mean()) if not vals.empty else 7.2


def list_ids_dates(features_df: pd.DataFrame) -> Tuple[List[str], Dict[str, List[str]]]:
    if features_df.empty:
        return [], {}

    f = features_df.dropna(subset=["Id", "log_date"]).copy()
    f["Id"] = f["Id"].astype(int).astype(str)

    ids = sorted(f["Id"].unique().tolist())
    by_id: Dict[str, List[str]] = {}
    for sid in ids:
        dates = f[f["Id"] == sid]["log_date"].dropna().astype(str).unique().tolist()
        by_id[sid] = sorted(dates)
    return ids, by_id


def get_wearable_context(features_df: pd.DataFrame, selected_id: str, selected_date: str) -> Dict[str, float]:
    if features_df.empty:
        return {}

    f = features_df.copy()
    f["Id"] = f["Id"].astype(int).astype(str)
    row = f[(f["Id"] == selected_id) & (f["log_date"].astype(str) == selected_date)]
    if row.empty:
        return {}

    rec = row.iloc[0].to_dict()
    out: Dict[str, float] = {}
    for k, v in rec.items():
        if k in ["Id", "log_date"]:
            continue
        out[k] = float(v) if pd.notna(v) else 0.0
    return out


def suggest_activity_from_wearable(context: Dict[str, float]) -> str:
    very = context.get("very_active_mins", 0)
    fairly = context.get("fairly_active_mins", 0)
    minute_int = context.get("minute_intensity_mean", 0)
    if very >= 35 or minute_int >= 2.2:
        return "Gym"
    if fairly >= 25 or minute_int >= 1.6:
        return "Yoga"
    return "Walking"


def wearable_enhancement(context: Dict[str, float], baseline_sleep_h: float) -> Dict[str, float]:
    steps = max(context.get("steps_total", 0), context.get("minute_steps_sum", 0) / 1000.0)
    cals = max(context.get("calories_burned", 0), context.get("hourly_calories_sum", 0))
    sleep_mins = context.get("sleep_mins", baseline_sleep_h * 60)
    hr = context.get("avg_heart_rate", 78)
    mets = context.get("avg_mets", 1.5)

    calorie_boost = max(0.0, (cals - 1900) * 0.12)

    protein_boost = 0.0
    if steps > 9000:
        protein_boost += 4
    if steps > 13000:
        protein_boost += 4
    if mets > 2.2:
        protein_boost += 2

    fatigue_adjust = 0.0
    sleep_deficit = max(0.0, baseline_sleep_h * 60 - sleep_mins)
    fatigue_adjust += sleep_deficit / 60
    if hr > 88:
        fatigue_adjust += 1.0

    sunlight_proxy = min(45.0, max(0.0, steps / 350.0))

    return {
        "calorie_boost": round(calorie_boost, 1),
        "protein_boost": round(protein_boost, 1),
        "fatigue_adjust": round(fatigue_adjust, 2),
        "sunlight_proxy": round(sunlight_proxy, 1),
        "sleep_mins": round(sleep_mins, 1),
        "steps_total": round(steps, 1),
        "avg_heart_rate": round(hr, 1),
    }
