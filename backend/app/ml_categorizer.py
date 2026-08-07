"""
Expense categorization service.

v2 model needs BOTH merchant_raw text AND amount to predict —
amount improved separation for price-distinctive categories
like rent/recharge (see notebook results: F1 0.9459 vs 0.9294 text-only).
"""
import os
import joblib

ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "categorizer.pkl")

_KEYWORD_MAP = {
    "food": ["swiggy", "zomato", "dominos", "mess", "canteen", "restaurant"],
    "transport": ["ola", "uber", "irctc", "rapido", "petrol", "fuel", "bus", "metro"],
    "shopping": ["amazon", "flipkart", "myntra", "meesho"],
    "entertainment": ["netflix", "spotify", "bookmyshow", "prime video", "hotstar"],
    "rent": ["rent", "landlord", "pg fee", "hostel fee"],
    "recharge": ["recharge", "jio", "airtel", "vi prepaid"],
    "education": ["udemy", "coursera", "exam fee", "college fee"],
}

_model = None
if os.path.exists(ARTIFACT_PATH):
    _model = joblib.load(ARTIFACT_PATH)


def categorize_transaction(merchant_raw: str, amount: float) -> tuple[str, float]:
    """Returns (category, confidence_score). Keeps your original function name
    so the router call site barely changes."""
    if _model is not None:
        pred = _model.predict([merchant_raw], [amount])[0]
        proba = _model.predict_proba([merchant_raw], [amount]).max()
        return pred, float(proba)

    # Fallback — only hit if categorizer.pkl is missing
    text = merchant_raw.lower()
    for category, keywords in _KEYWORD_MAP.items():
        if any(kw in text for kw in keywords):
            return category, 0.6
    return "uncategorized", 0.3