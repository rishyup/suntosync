from typing import Dict, List

import altair as alt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt


def as_dataframe(history_rows: List[Dict]) -> pd.DataFrame:
    if not history_rows:
        return pd.DataFrame()
    df = pd.DataFrame(history_rows)
    if "log_date" in df.columns:
        df["log_date"] = pd.to_datetime(df["log_date"], errors="coerce")
        df = df.sort_values("log_date")
    return df


def trend_30_day(df: pd.DataFrame):
    if df.empty:
        return None
    d = df.tail(30)
    fig = px.line(d, x="log_date", y=["health_score", "alignment_score"], markers=True)
    fig.update_layout(title="30-Day Circadian Trend", legend_title="Score Type")
    return fig


def sunlight_fatigue_corr(df: pd.DataFrame):
    if df.empty or "sunlight" not in df.columns or "fatigue" not in df.columns:
        return None, None
    corr = float(df[["sunlight", "fatigue"]].corr().iloc[0, 1]) if len(df) > 1 else 0.0
    fig = px.scatter(df, x="sunlight", y="fatigue", trendline="ols", title="Sunlight vs Fatigue")
    return fig, corr


def activity_impact(df: pd.DataFrame):
    if df.empty or "activity" not in df.columns:
        return None
    grouped = df.groupby("activity", as_index=False)["alignment_score"].mean()
    fig = px.bar(grouped, x="activity", y="alignment_score", color="activity", title="Activity Impact on Alignment")
    return fig


def nap_vs_productivity(df: pd.DataFrame):
    if df.empty:
        return None
    fig = px.scatter(df, x="nap_duration", y="alignment_score", color="fatigue", title="Nap vs Productivity Proxy")
    return fig


def meal_impact_heatmap(df: pd.DataFrame):
    if df.empty:
        return None
    data = df[["dinner_calories", "dinner_protein", "health_score", "alignment_score", "fatigue", "sunlight"]].copy()
    data = data.fillna(0)

    corr = data.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.heatmap(corr, annot=True, cmap="YlGnBu", ax=ax)
    ax.set_title("Meal Impact Heatmap")
    return fig


def circadian_gauge(value: int, title: str):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            title={"text": title},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#0b7a57"},
                "steps": [
                    {"range": [0, 50], "color": "#ffd7d7"},
                    {"range": [50, 75], "color": "#fff0c7"},
                    {"range": [75, 100], "color": "#d8f6ea"},
                ],
            },
        )
    )
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def factor_weight_chart(factors: Dict[str, float]):
    d = pd.DataFrame({"Factor": list(factors.keys()), "Score": list(factors.values())})
    chart = alt.Chart(d).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        x=alt.X("Factor:N", sort="-y"),
        y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 25])),
        color=alt.Color("Factor:N", legend=None),
        tooltip=["Factor", "Score"],
    ).properties(title="Circadian Alignment Factors")
    return chart
