"""
Synthetic intent dataset for the Kuber chatbot.

Each intent is described by phrase templates with {cat} / {tf} slots, filled
with category synonyms and timeframe phrasings, then augmented with casual
prefixes, casing changes, dropped punctuation and light typos — the way
students actually type into a chat box.

A separate HANDWRITTEN_TEST set (phrasings never produced by the templates)
is used for evaluation so the reported accuracy isn't just template recall.
"""
import random

INTENTS = [
    "budget_help",
    "category_query",
    "forecast_query",
    "help",
    "income_query",
    "investment_query",
    "random_chat",
    "savings_flex",
    "spending_complaint",
    "top_category",
    "total_spend",
]

CATEGORY_WORDS = {
    "food": ["food", "swiggy", "zomato", "eating out", "restaurants", "takeout", "snacks", "coffee", "groceries"],
    "transport": ["transport", "uber", "ola", "cabs", "travel", "bus", "metro", "rapido", "auto"],
    "shopping": ["shopping", "amazon", "flipkart", "clothes", "myntra", "online shopping"],
    "entertainment": ["entertainment", "netflix", "movies", "spotify", "concerts", "gaming"],
    "recharge": ["recharge", "jio", "airtel", "phone bill", "mobile data", "wifi"],
    "education": ["education", "courses", "college fees", "books", "stationery", "udemy"],
    "rent": ["rent", "hostel", "pg", "room rent"],
    "misc": ["misc", "random stuff", "other stuff", "miscellaneous"],
}

ASSETS = ["etfs", "bonds", "ppf", "mutual funds", "index funds", "gold", "stocks", "crypto", "fds", "nps", "reits"]

TIMEFRAMES = ["", "this week", "this month", "today", "last week", "last month", "so far", "lately", "in total"]

TEMPLATES = {
    "category_query": [
        "how much did i spend on {cat} {tf}",
        "how much have i spent on {cat} {tf}",
        "what did i spend on {cat} {tf}",
        "{cat} spending {tf}",
        "total {cat} spend {tf}",
        "show me my {cat} expenses {tf}",
        "how much money went to {cat} {tf}",
        "what's my {cat} total {tf}",
        "{cat} total {tf}?",
        "tell me my {cat} spending {tf}",
        "check my {cat} spend {tf}",
        "how much on {cat} {tf}",
        "what have i paid for {cat} {tf}",
        "give me the {cat} number {tf}",
        "spent on {cat} {tf}?",
    ],
    "spending_complaint": [
        "i spent way too much on {cat} {tf}",
        "i'm broke because of {cat}",
        "why do i keep wasting money on {cat}",
        "{cat} is draining my wallet",
        "ugh too much {cat} {tf}",
        "i need to stop spending on {cat}",
        "i overspent on {cat} again",
        "my {cat} spending is out of control",
        "i feel bad about how much i spent on {cat}",
        "{cat} is killing my budget",
        "i can't stop ordering {cat}",
        "regretting all that {cat} {tf}",
        "help i'm addicted to {cat}",
        "i blew so much money on {cat} {tf}",
    ],
    "budget_help": [
        "how much should i spend on {cat} {tf}",
        "set a budget for {cat}",
        "what's a good budget for {cat}",
        "help me budget for {cat}",
        "how do i cut down on {cat}",
        "give me a {cat} limit {tf}",
        "what should my {cat} budget be",
        "can you make me a budget",
        "help me plan my budget {tf}",
        "how can i spend less on {cat}",
        "suggest a spending limit for {cat}",
        "how should i split my money {tf}",
        "plan my spending {tf}",
        "what's a realistic budget for me",
    ],
    "savings_flex": [
        "how much am i saving {tf}",
        "how much can i save {tf}",
        "am i saving enough",
        "what are my savings {tf}",
        "how much will i have left {tf}",
        "projected savings {tf}",
        "can i save money {tf}",
        "how much money will i save",
        "am i doing good with savings",
        "how much is left after expenses",
        "what's my savings looking like",
        "will i have anything left at the end of the month",
        "i saved money {tf} right?",
        "how much can i put aside {tf}",
    ],
    "investment_query": [
        "where should i invest",
        "should i start a sip",
        "what are good mutual funds for beginners",
        "how do i start investing",
        "is investing in stocks a good idea",
        "what is an index fund",
        "should i invest in crypto",
        "how much should i invest monthly",
        "what's a sip",
        "best way to grow my money",
        "should i buy gold",
        "is a fixed deposit worth it",
        "how do mutual funds work",
        "which fund should i pick",
        "can i invest with 500 rupees",
        "what is nifty 50",
        "are {asset} worth it",
        "should i put money in {asset}",
        "is {asset} good for beginners",
        "tell me about {asset}",
        "{asset} or savings account",
    ],
    "total_spend": [
        "how much did i spend {tf}",
        "what's my total spending {tf}",
        "total expenses {tf}",
        "how much have i spent overall {tf}",
        "what did i spend in total {tf}",
        "show my spending {tf}",
        "how much money did i spend {tf}",
        "what are my total expenses {tf}",
        "overall spend {tf}",
        "sum of my spending {tf}",
        "how much did i blow {tf}",
        "what's my spend {tf}",
        "how much went out {tf}",
        "add up everything i spent {tf}",
        "all expenses combined {tf}",
        "grand total of my spending",
        "what's the total damage {tf}",
    ],
    "top_category": [
        "where does most of my money go",
        "what do i spend the most on {tf}",
        "biggest expense {tf}",
        "what's my top spending category",
        "which category do i spend the most on",
        "where am i spending the most {tf}",
        "what's eating my money",
        "top expenses {tf}",
        "break down my spending {tf}",
        "spending breakdown {tf}",
        "what are my biggest costs",
        "which category is highest {tf}",
        "where is my money going",
        "give me a category breakdown",
    ],
    "forecast_query": [
        "how much will i spend next week",
        "predict my spending",
        "what's my forecast",
        "forecast my expenses",
        "how much will i spend on {cat} next week",
        "what will next week look like",
        "expected spending next week",
        "predict my {cat} spending",
        "how much am i likely to spend",
        "projected expenses for next week",
        "what's coming up next week money wise",
        "estimate my next week spend",
    ],
    "income_query": [
        "how much do i earn",
        "what's my income",
        "how much money do i make {tf}",
        "what's my weekly income",
        "show my income sources",
        "how much do i get per month",
        "what's my allowance",
        "how much money comes in {tf}",
        "total income {tf}",
        "what are my earnings",
        "how much pocket money do i have",
        "what did i earn {tf}",
        "how much cash do i have coming in",
        "money coming in per month",
        "how much am i getting {tf}",
        "what's my monthly inflow",
    ],
    "help": [
        "what can you do",
        "how do you work",
        "what can i ask you",
        "help",
        "what are your features",
        "how do i use this",
        "what questions can i ask",
        "what do you know about me",
        "show me what you can do",
        "what are you",
        "who are you",
        "what is kuber",
    ],
    "random_chat": [
        "hi",
        "hello",
        "hey",
        "yo",
        "good morning",
        "sup",
        "thanks",
        "thank you",
        "thx",
        "lol",
        "ok cool",
        "nice",
        "bye",
        "see you",
        "you're awesome",
        "haha",
        "how are you",
        "what's up",
        "good night",
        "ok",
        "great thanks",
        "love this",
        "hmm",
    ],
}

PREFIXES = ["", "", "", "hey ", "yo ", "kuber ", "can you tell me ", "quick question ", "pls ", "bro ", "ok so "]
SUFFIXES = ["", "", "", "?", "??", " pls", " lol", " fr", "!"]


def _typo(text: str, rng: random.Random) -> str:
    if len(text) < 6:
        return text
    i = rng.randrange(1, len(text) - 1)
    op = rng.choice(["drop", "swap", "dup"])
    if op == "drop":
        return text[:i] + text[i + 1:]
    if op == "swap":
        return text[:i] + text[i + 1] + text[i] + text[i + 2:]
    return text[:i] + text[i] + text[i:]


def _fill(template: str, rng: random.Random) -> str:
    cat = rng.choice(rng.choice(list(CATEGORY_WORDS.values())))
    tf = rng.choice(TIMEFRAMES)
    asset = rng.choice(ASSETS)
    return " ".join(template.format(cat=cat, tf=tf, asset=asset).split())


def _augment(text: str, rng: random.Random) -> str:
    text = rng.choice(PREFIXES) + text + rng.choice(SUFFIXES)
    r = rng.random()
    if r < 0.15:
        text = text.capitalize()
    elif r < 0.2:
        text = text.upper()
    if rng.random() < 0.12:
        text = _typo(text, rng)
    if rng.random() < 0.3:
        text = text.replace("'", "")
    return text.strip()


def generate(per_intent: int = 400, seed: int = 42) -> list[tuple[str, str]]:
    rng = random.Random(seed)
    rows = []
    for intent, templates in TEMPLATES.items():
        seen = set()
        attempts = 0
        while len(seen) < per_intent and attempts < per_intent * 30:
            attempts += 1
            text = _augment(_fill(rng.choice(templates), rng), rng)
            if text.lower() not in seen:
                seen.add(text.lower())
                rows.append((text, intent))
    rng.shuffle(rows)
    return rows


# Phrasings written by hand, deliberately NOT derivable from TEMPLATES.
HANDWRITTEN_TEST = [
    ("how much have swiggy orders cost me", "category_query"),
    ("what's the damage on uber this month", "category_query"),
    ("netflix + spotify total?", "category_query"),
    ("rent paid so far", "category_query"),
    ("amount spent on books", "category_query"),
    ("zomato has ruined me", "spending_complaint"),
    ("why am i like this, another amazon order", "spending_complaint"),
    ("my shopping habit is embarrassing", "spending_complaint"),
    ("i keep taking cabs everywhere and it's costing me", "spending_complaint"),
    ("cap my food spending for me", "budget_help"),
    ("i want to spend less on travel, what limit", "budget_help"),
    ("make a weekly plan for my money", "budget_help"),
    ("what's a sensible amount for entertainment", "budget_help"),
    ("will i have money saved by sunday", "savings_flex"),
    ("am i on track to save this month", "savings_flex"),
    ("what's left over after all my bills", "savings_flex"),
    ("is an sip better than an fd", "investment_query"),
    ("where do i put 1000 rupees to grow it", "investment_query"),
    ("are etfs good for students", "investment_query"),
    ("should i get into the stock market", "investment_query"),
    ("how much money have i gone through this week", "total_spend"),
    ("all my expenses added up", "total_spend"),
    ("whats my spending this month in total", "total_spend"),
    ("what category takes the biggest chunk", "top_category"),
    ("rank my expenses", "top_category"),
    ("which thing costs me the most", "top_category"),
    ("what will i spend in the coming week", "forecast_query"),
    ("can you predict next week's food bill", "forecast_query"),
    ("expected expenses ahead", "forecast_query"),
    ("how much money am i bringing in", "income_query"),
    ("what's my salary from tutoring", "income_query"),
    ("total earnings per week", "income_query"),
    ("what kind of questions do you answer", "help"),
    ("how does this bot work", "help"),
    ("heyy", "random_chat"),
    ("thanks a lot!", "random_chat"),
    ("cool cool", "random_chat"),
    ("good evening", "random_chat"),
]
