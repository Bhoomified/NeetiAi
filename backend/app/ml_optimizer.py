"""
Budget optimizer — quadratic priority-weighted allocation (SLSQP).
savings_target_pct is ALWAYS supplied by the caller (per-request from the user),
never hardcoded or stored as a fixed model parameter.
"""
import os
import json
import numpy as np
from scipy.optimize import minimize

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "optimizer_config.json")

_DEFAULT_WEIGHTS = {
    "rent": 10, "education": 6, "recharge": 5, "food": 5,
    "transport": 4, "misc": 2, "shopping": 1, "entertainment": 1,
}
_MIN_PCT_OF_PREDICTED = 0.5

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        _config = json.load(f)
    _DEFAULT_WEIGHTS = _config.get("default_weights", _DEFAULT_WEIGHTS)
    _MIN_PCT_OF_PREDICTED = _config.get("min_pct_of_predicted", _MIN_PCT_OF_PREDICTED)


def optimize_budget(predicted_category_spend: dict, weekly_income: float,
                     savings_target_pct: float, category_weights: dict = None) -> tuple[dict | None, str | None]:
    if not predicted_category_spend:
        return None, "No spending history to build a budget from yet."
    if not (0 <= savings_target_pct < 1):
        return None, "savings_target_pct must be between 0 and 1 (e.g. 0.15 for 15%)."

    categories = list(predicted_category_spend.keys())
    n = len(categories)
    predicted = np.array([predicted_category_spend[c] for c in categories], dtype=float)

    weights = category_weights or _DEFAULT_WEIGHTS
    w = np.array([weights.get(c, 2) for c in categories], dtype=float)

    savings_amount = weekly_income * savings_target_pct
    budget_cap = weekly_income - savings_amount

    lower_bounds = predicted * _MIN_PCT_OF_PREDICTED
    upper_bounds = predicted.copy()

    if lower_bounds.sum() > budget_cap:
        return None, (f"Not feasible even at minimum spend — floor total ₹{lower_bounds.sum():.0f} "
                       f"exceeds available budget ₹{budget_cap:.0f}. Try a lower savings target.")

    def objective(x):
        gap = predicted - x
        return np.sum(w * gap**2)

    constraints = [{"type": "ineq", "fun": lambda x: budget_cap - np.sum(x)}]
    bounds = list(zip(lower_bounds, upper_bounds))
    x0 = predicted * 0.8

    result = minimize(objective, x0, method="SLSQP", bounds=bounds, constraints=constraints)
    if not result.success:
        return None, f"Optimizer failed to converge: {result.message}"

    allocations = []
    for i, cat in enumerate(categories):
        cap = round(float(result.x[i]), 2)
        cut_pct = round((predicted[i] - cap) / predicted[i] * 100, 1) if predicted[i] > 0 else 0.0
        allocations.append({
            "category": cat, "predicted_amount": round(float(predicted[i]), 2),
            "budget_cap": cap, "cut_percent": cut_pct,
        })

    total_allocated = sum(a["budget_cap"] for a in allocations)
    actual_savings = weekly_income - total_allocated

    return {
        "weekly_income": round(weekly_income, 2),
        "savings_target": round(savings_amount, 2),
        "projected_savings": round(actual_savings, 2),
        "target_met": actual_savings >= savings_amount * 0.95,
        "allocations": allocations,
    }, None