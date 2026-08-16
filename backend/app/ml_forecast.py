"""
Weekly spend forecasting service.

Rebuilds the same weekly aggregation + lag-feature logic from the training
notebook, but operating on live transaction rows from the DB instead of a CSV.
Models are plain RandomForestRegressor objects — no custom wrapper classes,
so this never hits the __main__ pickling issue the categorizer had.
"""
import os
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "ml", "artifacts")

_total_model = None
_category_models = {}
_metadata = {}

total_path = os.path.join(ARTIFACT_DIR, "weekly_total_model.pkl")
category_path = os.path.join(ARTIFACT_DIR, "weekly_category_models.pkl")
metadata_path = os.path.join(ARTIFACT_DIR, "forecast_metadata.json")

if os.path.exists(total_path):
    _total_model = joblib.load(total_path)
    print(f"✅ Loaded weekly total-spend model from {total_path}")
else:
    print(f"⚠️  No weekly total model found at {total_path} — forecasts will use rolling average")

if os.path.exists(category_path):
    _category_models = joblib.load(category_path)
    print(f"✅ Loaded {len(_category_models)} weekly category models")

if os.path.exists(metadata_path):
    with open(metadata_path) as f:
        _metadata = json.load(f)

FEATURE_COLS = _metadata.get("feature_cols", [
    "lag_1", "lag_2", "lag_3", "lag_4", "rolling_mean_4", "week_of_month", "is_first_week"
])


def _transactions_to_weekly_df(transactions: list, category: str = None) -> pd.DataFrame:
    """transactions: list of Transaction ORM rows (or dicts with date/amount/category)."""
    rows = [
        {"date": t.date, "amount": t.amount, "category": t.category}
        for t in transactions
        if category is None or t.category == category
    ]
    if not rows:
        return pd.DataFrame(columns=["ds", "y"])

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    weekly = df.set_index("date")["amount"].resample("W-MON").sum().reset_index()
    weekly.columns = ["ds", "y"]
    return weekly


def _build_feature_row(weekly_df: pd.DataFrame) -> dict | None:
    """Builds the single feature row needed to predict the NEXT week,
    using the most recent completed weeks as lag_1..lag_4."""
    if len(weekly_df) < 4:
        return None  # not enough history for lag_4 — caller should fall back

    weekly_df = weekly_df.sort_values("ds")
    recent = weekly_df["y"].values[-4:][::-1]  # most recent first: lag_1, lag_2, lag_3, lag_4

    next_week_date = weekly_df["ds"].max() + pd.Timedelta(days=7)
    day_of_month = next_week_date.day
    week_of_month = min((day_of_month - 1) // 7 + 1, 4)

    return {
        "lag_1": recent[0], "lag_2": recent[1], "lag_3": recent[2], "lag_4": recent[3],
        "rolling_mean_4": weekly_df["y"].values[-4:].mean(),
        "week_of_month": week_of_month,
        "is_first_week": 1 if week_of_month == 1 else 0,
    }


def forecast_user(transactions: list) -> dict:
    """
    Main entrypoint. transactions: all of a user's Transaction rows.
    Returns predicted total for next week + per-category breakdown.
    """
    weekly_total_df = _transactions_to_weekly_df(transactions)
    weeks_of_history = len(weekly_total_df)

    feat_row = _build_feature_row(weekly_total_df)

    if feat_row is not None and _total_model is not None:
        X = pd.DataFrame([feat_row])[FEATURE_COLS]
        predicted_total = max(0.0, float(_total_model.predict(X)[0]))
        total_method = "random_forest"
    else:
        # Fallback: rolling average of whatever history exists, or 0 if none
        predicted_total = float(weekly_total_df["y"].tail(4).mean()) if weeks_of_history > 0 else 0.0
        total_method = "rolling_average_fallback"

    # Category breakdown — try each category's own model if it beat naive during training,
    # else fall back to that category's historical share of total spend (from the notebook's approach)
    all_categories = {t.category for t in transactions if t.category}
    category_totals = {}
    for cat in all_categories:
        category_totals[cat] = sum(t.amount for t in transactions if t.category == cat)
    grand_total = sum(category_totals.values()) or 1.0

    categories_out = []
    for cat in all_categories:
        cat_weekly_df = _transactions_to_weekly_df(transactions, category=cat)
        cat_feat_row = _build_feature_row(cat_weekly_df)
        model_c = _category_models.get(cat)

        if cat_feat_row is not None and model_c is not None:
            X_c = pd.DataFrame([cat_feat_row])[FEATURE_COLS]
            predicted_cat = max(0.0, float(model_c.predict(X_c)[0]))
            method = "random_forest"
        else:
            share = category_totals[cat] / grand_total
            predicted_cat = round(predicted_total * share, 2)
            method = "rolling_average_fallback"

        categories_out.append({"category": cat, "predicted_amount": round(predicted_cat, 2), "method": method})

    return {
        "weeks_of_history": weeks_of_history,
        "predicted_total": round(predicted_total, 2),
        "total_method": total_method,
        "categories": categories_out,
    }