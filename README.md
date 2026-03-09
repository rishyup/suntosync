# Circadian-Metabolic Health Platform (No External API)

This platform now uses your full nutrition + wearable + sleep dataset bundle to improve scoring, recommendations, and analytics.

## Datasets now integrated

### Nutrition datasets
- `indianfoods.xlsx`
- `Indian_Food_Nutrition_Processed.csv`
- `IndianFoodDatasetCSV.csv`

### Wearable / health datasets
- `minuteMETsNarrow_merged.csv`
- `minuteSleep_merged.csv`
- `minuteStepsNarrow_merged.csv`
- `minuteStepsWide_merged.csv`
- `sleepDay_merged.csv`
- `weightLogInfo_merged.csv`
- `dailyActivity_merged.csv`
- `dailyCalories_merged.csv`
- `dailyIntensities_merged.csv`
- `dailySteps_merged.csv`
- `heartrate_seconds_merged.csv`
- `hourlyCalories_merged.csv`
- `hourlyIntensities_merged.csv`
- `hourlySteps_merged.csv`
- `minuteCaloriesNarrow_merged.csv`
- `minuteCaloriesWide_merged.csv`
- `minuteIntensitiesNarrow_merged.csv`
- `minuteIntensitiesWide_merged.csv`
- `Sleep Health and Lifestyle Dataset.xlsx`

## How these improve the model

- Builds a fused daily wearable feature table per `Id + date`
- Uses steps, calories, active minutes, sleep minutes, heart rate, METs, and weight signals
- Enhances model inputs automatically:
  - fatigue adjustment
  - sunlight proxy
  - activity inference
  - calorie/protein target boosts for meal planning
- Uses Sleep Health dataset for baseline sleep reference

## New module added

- `models/wearable_fusion.py` for loading, harmonizing, and feature fusion across all listed wearable datasets

## Architecture

```text
project/
├── app.py
├── analytics/
│   └── trend_analysis.py
├── models/
│   ├── circadian_model.py
│   ├── coach_engine.py
│   └── wearable_fusion.py
├── recommendations/
│   └── meal_engine.py
├── database/
│   └── db_manager.py
├── reports/
│   └── report_generator.py
├── utils/
│   ├── auth.py
│   └── scoring.py
└── requirements.txt
```

## Dataset paths checked by code

1. `C:\Users\PC\Downloads\archive (1)\<filename>`
2. Project folder (same directory as `app.py`)

If some files are missing, the app still runs with available data and fallbacks.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Notes

- No external API calls are used.
- Data remains local in SQLite (`circadian_tracker.db`).
