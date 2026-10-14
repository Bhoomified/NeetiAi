"""
Chatbot service: DistilBERT intent classification + regex entity extraction
+ data-grounded response generation.

Design principle: the model NEVER generates response text or numbers directly —
it only classifies intent. Every figure in a reply is computed here from the
user's real transactions, income sources and forecast; the wording comes from
handlers below. This guarantees the bot can't hallucinate a financial figure.

Low-confidence predictions fall back to keyword rules instead of a generic
"not sure", so short or oddly phrased questions still get a real answer.
"""
import os
import re
import random
from collections import defaultdict
from datetime import datetime, timedelta

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

CONFIDENCE_THRESHOLD = 0.55

_tokenizer = None
_model = None
_label_encoder = None

if os.path.exists(MODEL_DIR) and os.path.exists(ENCODER_PATH):
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    _model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
    _model.eval()
    _label_encoder = joblib.load(ENCODER_PATH)
    print(f"✅ Loaded DistilBERT intent classifier from {MODEL_DIR} ({len(_label_encoder.classes_)} intents)")
else:
    print(f"⚠️  Chatbot model not found at {MODEL_DIR} — /chat will use keyword rules only")


CATEGORY_KEYWORDS = {
    "food": ["food", "swiggy", "zomato", "eating", "restaurant", "takeout", "snack", "coffee", "grocer", "lunch", "dinner"],
    "transport": ["transport", "uber", "ola", "travel", "bus", "cab", "metro", "rapido", "auto", "petrol", "fuel"],
    "shopping": ["shopping", "amazon", "flipkart", "clothes", "myntra", "meesho"],
    "entertainment": ["entertainment", "netflix", "movie", "spotify", "concert", "gaming", "prime video", "hotstar"],
    "recharge": ["recharge", "jio", "airtel", "data", "wifi", "phone bill", "mobile"],
    "education": ["education", "course", "fees", "book", "stationery", "udemy", "tuition"],
    "rent": ["rent", "hostel", "pg"],
    "misc": ["misc", "random stuff", "other stuff"],
}

TIMEFRAME_LABELS = {
    "today": "today",
    "yesterday": "yesterday",
    "week": "this week",
    "last_week": "last week",
    "month": "this month",
    "last_month": "last month",
    None: "so far",
}


# ---------- entity extraction ----------

def extract_amount(text):
    match = re.search(r"(?:₹|rs\.?\s?)?\s?(\d+(?:,\d+)*(?:\.\d+)?)\s?(?:k\b)?", text.lower())
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    if re.search(rf"{re.escape(match.group(1))}\s?k\b", text.lower()):
        value *= 1000
    return value


def extract_category(text):
    text_lower = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(re.search(rf"\b{re.escape(kw)}", text_lower) for kw in keywords):
            return category
    return None


def extract_timeframe(text):
    t = text.lower()
    if "yesterday" in t:
        return "yesterday"
    if "today" in t:
        return "today"
    if re.search(r"(last|previous|past) week", t):
        return "last_week"
    if re.search(r"(last|previous|past) month", t):
        return "last_month"
    if "week" in t:
        return "week"
    if "month" in t:
        return "month"
    return None


# ---------- intent ----------

def predict_intent(text: str) -> tuple[str, float]:
    if _model is None:
        return "unclear", 0.0
    inputs = _tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=32)
    with torch.no_grad():
        probs = torch.softmax(_model(**inputs).logits, dim=-1)
        pred_idx = probs.argmax().item()
        confidence = probs.max().item()
    intent = _label_encoder.inverse_transform([pred_idx])[0]
    return intent, confidence


def _rule_intent(text: str, category) -> str | None:
    """Keyword fallback used when the classifier isn't confident."""
    t = text.lower()
    if re.search(r"\b(sip|invest|mutual fund|index fund|stock|share market|crypto|gold|fd|fixed deposit|etf|nifty)\b", t):
        return "investment_query"
    if re.search(r"\b(income|earn|salary|allowance|pocket money|stipend)\b", t):
        return "income_query"
    if re.search(r"\b(next week|predict|forecast|expect)\b", t):
        return "forecast_query"
    if re.search(r"\b(save|saving|savings|left over|leftover)\b", t):
        return "savings_flex"
    if re.search(r"\b(budget|limit|cap|cut down|plan)\b", t):
        return "budget_help"
    if re.search(r"\b(most|biggest|top|breakdown|where.*money)\b", t):
        return "top_category"
    if re.search(r"\b(spend|spent|spending|expense|cost|paid)\b", t):
        return "category_query" if category else "total_spend"
    if category:
        return "category_query"
    if re.search(r"\b(help|what can you|how do you)\b", t):
        return "help"
    if re.search(r"^(hi+|hey+|hello|yo|sup|thanks|thank you|thx|bye|ok|cool|lol)\b", t):
        return "random_chat"
    return None


# ---------- data helpers ----------

def inr(amount: float) -> str:
    """Indian digit grouping: 123456.7 -> ₹1,23,457"""
    n = int(round(amount))
    sign = "-" if n < 0 else ""
    s = str(abs(n))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = f"{head},{tail}"
    return f"{sign}₹{s}"


def _window(timeframe, now: datetime):
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    if timeframe == "today":
        return today, None
    if timeframe == "yesterday":
        return today - timedelta(days=1), today
    if timeframe == "week":
        return week_start, None
    if timeframe == "last_week":
        return week_start - timedelta(days=7), week_start
    if timeframe == "month":
        return month_start, None
    if timeframe == "last_month":
        return (month_start - timedelta(days=1)).replace(day=1), month_start
    return None, None


def _filter(transactions, timeframe, now):
    start, end = _window(timeframe, now)
    return [
        t for t in transactions
        if (start is None or t.date >= start) and (end is None or t.date < end)
    ]


def _plural(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def _weekly_average(transactions, category=None) -> float | None:
    rows = [t for t in transactions if category is None or t.category == category]
    if not rows:
        return None
    span_days = (max(t.date for t in rows) - min(t.date for t in rows)).days
    weeks = max(1.0, span_days / 7)
    return sum(t.amount for t in rows) / weeks


def _by_category(transactions) -> list[tuple[str, float]]:
    totals = defaultdict(float)
    for t in transactions:
        totals[t.category or "misc"] += t.amount
    return sorted(totals.items(), key=lambda kv: kv[1], reverse=True)


# ---------- intent handlers ----------
# Each handler receives a ctx dict and returns the reply text.

def _no_data(ctx):
    tf = TIMEFRAME_LABELS[ctx["timeframe"]]
    if ctx["timeframe"] and ctx["all_transactions"]:
        return f"Nothing logged {tf}. Ask without a timeframe to see your all-time numbers."
    return "I don't see any transactions yet. Add a few on the Dashboard and I'll have real numbers for you."


def handle_category_query(ctx):
    cat, txns, tf = ctx["category"], ctx["transactions"], TIMEFRAME_LABELS[ctx["timeframe"]]
    if not cat:
        return handle_top_category(ctx)
    cat_txns = [t for t in txns if t.category == cat]
    if not cat_txns:
        return f"No {cat} spending logged {tf}. Nice restraint."
    cat_total = sum(t.amount for t in cat_txns)
    overall = sum(t.amount for t in txns)
    share = cat_total / overall * 100 if overall else 0
    biggest = max(cat_txns, key=lambda t: t.amount)
    return (
        f"You've spent {inr(cat_total)} on {cat} {tf} across {_plural(len(cat_txns), "transaction")} — "
        f"{share:.0f}% of your total. Biggest one: {inr(biggest.amount)} at {biggest.merchant_raw}."
    )


def handle_total_spend(ctx):
    txns, tf = ctx["transactions"], TIMEFRAME_LABELS[ctx["timeframe"]]
    if not txns:
        return _no_data(ctx)
    total = sum(t.amount for t in txns)
    top_cat, top_amt = _by_category(txns)[0]
    return (
        f"You've spent {inr(total)} {tf} across {_plural(len(txns), 'transaction')}. "
        f"The largest slice is {top_cat} at {inr(top_amt)}."
    )


def handle_top_category(ctx):
    txns, tf = ctx["transactions"], TIMEFRAME_LABELS[ctx["timeframe"]]
    if not txns:
        return _no_data(ctx)
    ranked = _by_category(txns)
    total = sum(a for _, a in ranked)
    top3 = ", ".join(f"{c} {inr(a)} ({a / total * 100:.0f}%)" for c, a in ranked[:3])
    return f"{tf[0].upper() + tf[1:]}, most of your money goes to {top3}. Total spent: {inr(total)}."


def handle_spending_complaint(ctx):
    cat, txns = ctx["category"], ctx["transactions"]
    if not txns:
        return _no_data(ctx)
    if not cat:
        cat = _by_category(txns)[0][0]
    cat_total = sum(t.amount for t in txns if t.category == cat)
    if not cat_total:
        return f"Actually, you've got no {cat} spending logged {TIMEFRAME_LABELS[ctx['timeframe']]} — you're being harder on yourself than the numbers are."
    weekly = _weekly_average(ctx["all_transactions"], cat)
    tip = (
        f" That's about {inr(weekly)} a week on average — try capping it at {inr(weekly * 0.8)} next week, a 20% trim."
        if weekly else ""
    )
    return f"Fair — {cat} is at {inr(cat_total)} {TIMEFRAME_LABELS[ctx['timeframe']]}.{tip}"


def handle_budget_help(ctx):
    cat = ctx["category"]
    forecast = ctx["forecast"]()
    if not forecast or not forecast["categories"]:
        return "I need a few weeks of transactions before I can suggest a budget. Add some on the Dashboard first."
    if cat:
        weekly = _forecast_for(ctx, cat)
        if not weekly:
            return f"You don't have enough {cat} history for me to set a limit yet."
        return (
            f"At your current pace you'd spend about {inr(weekly)} on {cat} next week. "
            f"A cap of {inr(weekly * 0.8)} is a realistic 20% trim."
        )
    plan = ctx["optimize"]()
    if not plan:
        return "Add your income on the Budget page and I'll build a full weekly plan around it."
    caps = ", ".join(f"{a['category']} {inr(a['budget_cap'])}" for a in sorted(plan["allocations"], key=lambda a: -a["budget_cap"])[:4])
    return (
        f"With {inr(plan['weekly_income'])}/week coming in, here's a plan: {caps}. "
        f"That leaves about {inr(plan['projected_savings'])} saved. Full breakdown is on the Budget page."
    )


def handle_savings_flex(ctx):
    weekly_income = ctx["income"]["weekly_income"]
    if not weekly_income:
        return "I don't know your income yet — add it on the Budget page and I'll tell you exactly what you can save."
    forecast = ctx["forecast"]()
    if not forecast or not forecast["predicted_total"]:
        return f"Your income is {inr(weekly_income)}/week, but I need some spending history to project savings."
    leftover = weekly_income - forecast["predicted_total"]
    if leftover <= 0:
        return (
            f"Heads up: you're on pace to spend {inr(forecast['predicted_total'])} next week against "
            f"{inr(weekly_income)} income — about {inr(-leftover)} over. Ask me for a budget and I'll find where to trim."
        )
    rate = leftover / weekly_income * 100
    verdict = "solid" if rate >= 20 else "decent, with room to grow" if rate >= 10 else "a bit thin"
    return (
        f"On current pace you'll keep about {inr(leftover)} next week — {rate:.0f}% of your income. "
        f"That's {verdict}."
    )


def handle_forecast_query(ctx):
    forecast = ctx["forecast"]()
    if not forecast or not forecast["categories"]:
        return "I need a few weeks of transactions before I can forecast. Keep logging and check back."
    cat = ctx["category"]
    if cat:
        weekly = _forecast_for(ctx, cat)
        if weekly is None:
            return f"Not enough {cat} history to forecast yet."
        return f"I expect you'll spend about {inr(weekly)} on {cat} next week."
    top = sorted(forecast["categories"], key=lambda c: -c["predicted_amount"])[:2]
    top_txt = " and ".join(f"{c['category']} ({inr(c['predicted_amount'])})" for c in top)
    return f"Next week's forecast: about {inr(forecast['predicted_total'])} in total, led by {top_txt}."


def handle_income_query(ctx):
    inc = ctx["income"]
    if not inc["weekly_income"]:
        return "You haven't added any income yet — head to the Budget page to add an allowance, stipend or side income."
    parts = [f"Your recurring income is {inr(inc['recurring_weekly_income'])}/week (about {inr(inc['recurring_weekly_income'] * 4.33)}/month)."]
    if inc["one_time_total"]:
        parts.append(f"Plus {inr(inc['one_time_total'])} in one-time income.")
    return " ".join(parts)


INVESTMENT_NOTES = [
    (r"\bsip\b", "A SIP puts a fixed amount into a mutual fund every month — it averages out market ups and downs and builds the habit. You can start with ₹500."),
    (r"index|nifty|etf", "Index funds track a market index like the Nifty 50. They're low-cost, diversified, and a sensible core for a beginner."),
    (r"crypto|bitcoin", "Crypto is highly volatile and lightly regulated in India — if at all, keep it to a small slice you can afford to lose."),
    (r"\bfd\b|fixed deposit", "FDs are safe and predictable but usually only just beat inflation. Good for an emergency fund, not long-term growth."),
    (r"gold", "Gold is a hedge, not a growth engine. Sovereign Gold Bonds or gold ETFs avoid making-charges if you want some exposure."),
    (r"stock|share", "Picking individual stocks takes research and stomach for swings. Most beginners do better starting with an index fund."),
]


def handle_investment_query(ctx):
    t = ctx["message"].lower()
    note = next((n for pattern, n in INVESTMENT_NOTES if re.search(pattern, t)), None)
    if note is None:
        note = "For most students, an emergency fund first, then a monthly SIP in a Nifty 50 index fund, is a calm, low-cost place to start."
    amount = ctx["amount"]
    if amount and 100 <= amount <= 1_000_000:
        fv = amount * (((1 + 0.01) ** 60 - 1) / 0.01) * 1.01
        note += f" For scale: {inr(amount)}/month for 5 years at an assumed 12%/yr grows to roughly {inr(fv)}."
    return note + " Your risk profile and fund ideas are on the Investments page. (General info, not personal financial advice.)"


def handle_help(ctx):
    return (
        "I can tell you what you've spent (overall or by category, for today, this week, last month…), "
        "where most of your money goes, what you'll likely spend next week, how much you can save, "
        "suggest budget caps, and explain investing basics. Try: \"how much on food this month?\""
    )


def handle_random_chat(ctx):
    t = ctx["message"].lower()
    if re.search(r"thank|thx|ty\b|appreciate", t):
        return random.choice(["Anytime.", "Happy to help — ask me anything about your money.", "Of course."])
    if re.search(r"\bbye\b|see you|good night|later", t):
        return random.choice(["See you soon. Your ledger will be here.", "Take care — spend wisely."])
    if re.search(r"how are you", t):
        return "Doing well, thanks for asking. Want a quick look at your spending this week?"
    if not re.search(r"\b(hi+|hey+|hello|yo|sup|morning|evening|afternoon|what'?s up|hola|namaste)\b", t):
        return random.choice(["Ha, noted.", "Got it."]) if re.search(r"\b(lol|haha|ok|cool|nice|hmm)\b", t) else handle_fallback(ctx)
    return random.choice([
        "Hello. Ask me about your spending, budget, savings or investments.",
        "Hey — what would you like to know about your money today?",
    ])


def handle_fallback(ctx):
    return "I'm not quite sure what you mean. Try \"how much did I spend this week?\" or \"what can you do?\""


HANDLERS = {
    "category_query": handle_category_query,
    "total_spend": handle_total_spend,
    "top_category": handle_top_category,
    "spending_complaint": handle_spending_complaint,
    "budget_help": handle_budget_help,
    "savings_flex": handle_savings_flex,
    "forecast_query": handle_forecast_query,
    "income_query": handle_income_query,
    "investment_query": handle_investment_query,
    "help": handle_help,
    "random_chat": handle_random_chat,
}


def _forecast_for(ctx, category):
    forecast = ctx["forecast"]()
    if not forecast:
        return None
    match = next((c for c in forecast["categories"] if c["category"] == category), None)
    return match["predicted_amount"] if match else None


def _memo(fn):
    cache = []
    def wrapper():
        if not cache:
            cache.append(fn())
        return cache[0]
    return wrapper


def chat(user_message: str, transactions: list, income: dict, forecast_fn, optimize_fn, now: datetime = None) -> dict:
    """
    transactions: the user's Transaction rows
    income: output of compute_income_breakdown
    forecast_fn / optimize_fn: zero-arg callables, evaluated lazily (only the
    intents that need them pay for a forecast run)
    """
    now = now or datetime.utcnow()
    entities = {
        "amount": extract_amount(user_message),
        "category": extract_category(user_message),
        "timeframe": extract_timeframe(user_message),
    }

    intent, confidence = predict_intent(user_message)
    source = "model"
    if confidence < CONFIDENCE_THRESHOLD or intent not in HANDLERS:
        rule = _rule_intent(user_message, entities["category"])
        intent, source = (rule, "rules") if rule else ("unclear", "none")

    if intent in ("random_chat", "unclear") and entities["category"]:
        intent, source = "category_query", "rules"

    ctx = {
        "message": user_message,
        "category": entities["category"],
        "timeframe": entities["timeframe"],
        "amount": entities["amount"],
        "all_transactions": transactions,
        "transactions": _filter(transactions, entities["timeframe"], now),
        "income": income,
        "forecast": _memo(forecast_fn),
        "optimize": _memo(optimize_fn),
    }
    response = HANDLERS.get(intent, handle_fallback)(ctx)
    if intent not in ("help", "investment_query"):
        response = safe_rephrase(response)

    return {
        "intent": intent,
        "confidence": round(confidence, 3),
        "intent_source": source,
        "entities": entities,
        "response": response,
    }
