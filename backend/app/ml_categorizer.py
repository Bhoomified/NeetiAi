import os
import sys
import joblib
from app.ml.model_classes import TextAmountXGBWrapper, clean_text  # noqa: F401

ARTIFACT_PATH = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "categorizer.pkl")

# Register the class under __main__ so joblib's unpickler can resolve it —
# the pickle was saved from a notebook where this class lived in __main__
sys.modules["__main__"].TextAmountXGBWrapper = TextAmountXGBWrapper

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
    print(f"✅ Loaded trained categorizer from {ARTIFACT_PATH}")
else:
    print(f"⚠️  No trained model found at {ARTIFACT_PATH} — using keyword fallback")


def categorize_transaction(merchant_raw: str, amount: float) -> tuple[str, float]:
    if _model is not None:
        pred = _model.predict([merchant_raw], [amount])[0]
        proba = _model.predict_proba([merchant_raw], [amount]).max()
        return pred, float(proba)

    text = merchant_raw.lower()
    for category, keywords in _KEYWORD_MAP.items():
        if any(kw in text for kw in keywords):
            return category, 0.6
    return "uncategorized", 0.3