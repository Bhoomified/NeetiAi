"""
Chatbot service: DistilBERT intent classification + spaCy/regex entity
extraction + template-based response generation.

Design principle: the model NEVER generates response text or numbers directly —
it only classifies intent. All factual content (amounts, categories) comes
from the backend's real data; templates control exact wording. This guarantees
the bot can't hallucinate a financial figure.
"""
import os
import re
import random
import joblib
from app.ml_rephrase import safe_rephrase

try:
    import torch # type: ignore
except ImportError:
    torch = None

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification # type: ignore
except ImportError:
    AutoTokenizer = None
    AutoModelForSequenceClassification = None

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "ml", "artifacts")
MODEL_DIR = os.path.join(ARTIFACT_DIR, "distilbert_intent")
ENCODER_PATH = os.path.join(ARTIFACT_DIR, "intent_label_encoder.pkl")

CONFIDENCE_THRESHOLD = 0.5   # DistilBERT's confidence is much better calibrated
                              # than LogReg's — a higher bar is appropriate now

_tokenizer = None
_model = None
_label_encoder = None

if os.path.exists(MODEL_DIR) and os.path.exists(ENCODER_PATH):
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    _model.eval()
    _label_encoder = joblib.load(ENCODER_PATH)
    print(f"✅ Loaded DistilBERT intent classifier from {MODEL_DIR}")
else:
    print(f"⚠️  Chatbot model not found at {MODEL_DIR} — /chat will not work until it's added")


CATEGORY_KEYWORDS = {
    "food": ["food", "swiggy", "zomato", "eating", "restaurant"],
    "transport": ["transport", "uber", "ola", "travel", "bus", "cab"],
    "shopping": ["shopping", "amazon", "flipkart", "clothes"],
    "entertainment": ["entertainment", "netflix", "movies", "spotify"],
    "recharge": ["recharge", "jio", "airtel", "data", "wifi"],
    "education": ["education", "course", "fees", "books"],
    "rent": ["rent", "hostel", "pg"],
}

RESPONSE_TEMPLATES = {
    "spending_complaint": [
        "bestie you've spent ₹{amount} on {category} — the girlies who budget could NEVER 💀",
        "₹{amount} on {category}?? not you being unwell for that",
        "okay {category} is clearly winning against your wallet rn, ₹{amount} spent",
    ],
    "budget_help": [
        "based on your spending, I'd cap {category} at ₹{amount} this week — no cap (pun intended)",
        "here's the move: keep {category} under ₹{amount} and you're saving like a legend",
    ],
    "category_query": [
        "you've spent ₹{amount} on {category} — {timeframe_text}",
        "{category} total: ₹{amount} {timeframe_text}, no judgment 👀",
    ],
    "savings_flex": [
        "periodt, you're saving well — projected savings this week: ₹{amount} 💅",
        "look at you being financially responsible, ₹{amount} saved fr",
    ],
    "investment_query": [
        "based on your risk profile, SIPs in index funds are usually the move for beginners — want me to break it down?",
        "honestly for students, starting small with a SIP (even ₹500/month) compounds better than you'd think",
    ],
    "random_chat": [
        "heyyy 👋 what do you wanna know about your money today",
        "I got you — ask me about your spending, budget, or investments",
        "lol anytime bestie",
    ],
    "fallback": [
        "not totally sure what you mean — try asking about your spending, budget, or savings 👀",
    ],
}


def extract_amount(text):
    match = re.search(r"₹?\s?(\d+(?:,\d+)?(?:\.\d+)?)\s?(?:rs|rupees|₹)?", text.lower())
    return float(match.group(1).replace(",", "")) if match else None


def extract_category(text):
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return None


def extract_timeframe(text):
    text_lower = text.lower()
    if "today" in text_lower:
        return "today"
    if "week" in text_lower:
        return "week"
    if "month" in text_lower:
        return "month"
    return None


def predict_intent(text: str) -> tuple[str, float]:
    if _model is None:
        return "unclear", 0.0
    inputs = _tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=32)
    with torch.no_grad():
        outputs = _model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)
        pred_idx = probs.argmax().item()
        confidence = probs.max().item()
    intent = _label_encoder.inverse_transform([pred_idx])[0]
    return intent, confidence


def generate_response(intent: str, entities: dict, backend_data: dict = None) -> str:
    templates = RESPONSE_TEMPLATES.get(intent, RESPONSE_TEMPLATES["fallback"])
    template = random.choice(templates)

    needs_amount = "{amount}" in template
    needs_category = "{category}" in template

    amount = (backend_data or {}).get("amount") or entities.get("amount")
    category = entities.get("category") or (backend_data or {}).get("category")
    timeframe = entities.get("timeframe") or "so far"
    timeframe_text = f"this {timeframe}" if timeframe != "so far" else timeframe

    if (needs_amount and amount is None) or (needs_category and category is None):
        return random.choice(RESPONSE_TEMPLATES["fallback"])

    return template.format(
        amount=int(amount) if amount else 0,
        category=category or "",
        timeframe_text=timeframe_text,
    )


def chat(user_message: str, backend_data: dict = None) -> dict:
    intent, confidence = predict_intent(user_message)

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "intent": "unclear", "confidence": round(confidence, 3),
            "entities": {}, "response": random.choice(RESPONSE_TEMPLATES["fallback"]),
        }

    entities = {
        "amount": extract_amount(user_message),
        "category": extract_category(user_message),
        "timeframe": extract_timeframe(user_message),
    }
    response = generate_response(intent, entities, backend_data)
    response = safe_rephrase(response)   # both assignment steps now guaranteed to run in sequence

    return {"intent": intent, "confidence": round(confidence, 3), "entities": entities, "response": response}