from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

DATASET_PATHS = {
    "indianfoods.xlsx": [
        Path(r"C:\Users\PC\Downloads\archive (1)\indianfoods.xlsx"),
        Path(__file__).resolve().parent.parent / "indianfoods.xlsx",
    ],
    "Indian_Food_Nutrition_Processed.csv": [
        Path(r"C:\Users\PC\Downloads\archive (1)\Indian_Food_Nutrition_Processed.csv"),
        Path(__file__).resolve().parent.parent / "Indian_Food_Nutrition_Processed.csv",
    ],
    "IndianFoodDatasetCSV.csv": [
        Path(r"C:\Users\PC\Downloads\archive (1)\IndianFoodDatasetCSV.csv"),
        Path(__file__).resolve().parent.parent / "IndianFoodDatasetCSV.csv",
    ],
}

DEFAULT_MEAL_BANK = [
    {"dish": "Paneer Bhurji", "calories": 220, "protein": 18, "diet": "Vegetarian"},
    {"dish": "Dal Tadka", "calories": 180, "protein": 10, "diet": "Vegetarian"},
    {"dish": "Roti", "calories": 110, "protein": 3, "diet": "Vegetarian"},
    {"dish": "Cucumber Salad", "calories": 30, "protein": 1, "diet": "Vegetarian"},
    {"dish": "Fish Curry", "calories": 280, "protein": 26, "diet": "Non-Vegetarian"},
    {"dish": "Chicken Curry", "calories": 300, "protein": 28, "diet": "Non-Vegetarian"},
    {"dish": "Egg Bhurji", "calories": 210, "protein": 15, "diet": "Non-Vegetarian"},
    {"dish": "Sauteed Vegetables", "calories": 90, "protein": 3, "diet": "Vegetarian"},
]


def load_dataset_from_candidates(paths: List[Path], is_excel: bool) -> Tuple[Optional[pd.DataFrame], Optional[Path]]:
    for p in paths:
        try:
            if p.exists():
                df = pd.read_excel(p) if is_excel else pd.read_csv(p)
                return df, p
        except Exception:
            continue
    return None, None


def _normalized(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d.columns = [str(c).strip().lower() for c in d.columns]
    return d


def _find_col(columns: List[str], options: List[str]) -> Optional[str]:
    for o in options:
        if o in columns:
            return o
    return None


def build_nutrition_table() -> Tuple[pd.DataFrame, Dict[str, Optional[Path]]]:
    sources: Dict[str, Optional[Path]] = {}
    tables: List[pd.DataFrame] = []

    xlsx_df, xlsx_path = load_dataset_from_candidates(DATASET_PATHS["indianfoods.xlsx"], True)
    csv1_df, csv1_path = load_dataset_from_candidates(DATASET_PATHS["Indian_Food_Nutrition_Processed.csv"], False)
    csv2_df, csv2_path = load_dataset_from_candidates(DATASET_PATHS["IndianFoodDatasetCSV.csv"], False)

    sources["indianfoods.xlsx"] = xlsx_path
    sources["Indian_Food_Nutrition_Processed.csv"] = csv1_path
    sources["IndianFoodDatasetCSV.csv"] = csv2_path

    for raw in [xlsx_df, csv1_df, csv2_df]:
        if raw is None:
            continue
        df = _normalized(raw)
        cols = list(df.columns)

        dish_col = _find_col(cols, ["food", "food_name", "dish", "item", "name", "recipe", "meal"])
        cal_col = _find_col(cols, ["calories", "energy", "kcal", "calorie"])
        prot_col = _find_col(cols, ["protein", "proteins", "protein_g", "protein (g)"])

        if dish_col:
            out = pd.DataFrame()
            out["dish"] = df[dish_col].astype(str)
            out["calories"] = pd.to_numeric(df[cal_col], errors="coerce") if cal_col else None
            out["protein"] = pd.to_numeric(df[prot_col], errors="coerce") if prot_col else None
            tables.append(out)

    if tables:
        merged = pd.concat(tables, ignore_index=True)
        merged = merged.dropna(subset=["dish"]).copy()
        merged["dish"] = merged["dish"].str.strip()
        merged = merged[merged["dish"] != ""]

        merged["calories"] = merged["calories"].fillna(180)
        merged["protein"] = merged["protein"].fillna(8)
        merged["diet"] = merged["dish"].str.lower().apply(
            lambda x: "Non-Vegetarian" if any(k in x for k in ["fish", "chicken", "egg", "mutton"]) else "Vegetarian"
        )
        return merged[["dish", "calories", "protein", "diet"]], sources

    fallback = pd.DataFrame(DEFAULT_MEAL_BANK)
    return fallback, sources


def meal_quality_signals(breakfast: str, lunch: str) -> Dict[str, int]:
    text = f"{breakfast} {lunch}".lower()
    protein_keys = ["paneer", "dal", "chana", "rajma", "egg", "chicken", "fish", "curd", "sprouts"]
    fiber_keys = ["salad", "vegetable", "sabzi", "oats", "millet", "fruit", "beans"]
    refined_keys = ["maida", "poori", "paratha", "white bread", "noodles", "fried"]
    sugar_keys = ["dessert", "jalebi", "halwa", "cake", "cola", "sweet"]

    return {
        "protein_hits": sum(1 for k in protein_keys if k in text),
        "fiber_hits": sum(1 for k in fiber_keys if k in text),
        "refined_hits": sum(1 for k in refined_keys if k in text),
        "sugar_hits": sum(1 for k in sugar_keys if k in text),
    }


def personalized_dinner_plan(
    nutrition_df: pd.DataFrame,
    diet_pref: str,
    fatigue: int,
    activity: str,
    health_score_value: int,
    calorie_adjust: float = 0.0,
    protein_adjust: float = 0.0,
) -> Dict[str, object]:
    base_cal = 420
    if activity == "Gym":
        base_cal += 140
    elif activity == "Yoga":
        base_cal += 80
    else:
        base_cal += 60

    if fatigue >= 7:
        base_cal += 70

    target_calories = int(base_cal + max(0.0, calorie_adjust))
    target_protein = int((26 if diet_pref == "Vegetarian" else 32) + max(0.0, protein_adjust))

    candidates = nutrition_df[nutrition_df["diet"] == diet_pref].copy()
    if candidates.empty:
        candidates = nutrition_df.copy()

    candidates["score"] = (
        (candidates["protein"] - target_protein / 2).abs() * -0.7
        + (candidates["calories"] - target_calories / 3).abs() * -0.1
    )

    selected = candidates.sort_values("score", ascending=False).head(4)

    meal_names = selected["dish"].tolist()
    total_cal = float(selected["calories"].sum())
    total_protein = float(selected["protein"].sum())

    if len(meal_names) < 4:
        if diet_pref == "Vegetarian":
            meal_names = ["Paneer Bhurji", "Dal Tadka", "2 Rotis", "Cucumber Salad"]
            total_cal = 520
            total_protein = 28
        else:
            meal_names = ["Fish Curry", "Dal", "1 Roti", "Cucumber Salad"]
            total_cal = 560
            total_protein = 34

    readiness_note = "Recovery focus" if health_score_value < 60 else "Balanced performance focus"

    return {
        "items": meal_names,
        "calories": round(total_cal, 1),
        "protein": round(total_protein, 1),
        "target_calories": target_calories,
        "target_protein": target_protein,
        "meal_name": " | ".join(meal_names),
        "note": readiness_note,
    }
