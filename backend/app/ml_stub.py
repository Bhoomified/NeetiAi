def categorize_transaction(merchant_raw: str) -> str:
    text = merchant_raw.lower()

    rules = {
        "food": ["swiggy", "zomato", "restaurant", "cafe", "dominos"],
        "travel": ["uber", "ola", "irctc", "airlines", "redbus"],
        "shopping": ["amazon", "flipkart", "myntra", "amzn"],
        "utilities": ["electricity", "airtel", "jio", "recharge"],
        "groceries": ["bigbasket", "grofers", "dmart", "zepto"],
    }

    for category, keywords in rules.items():
        if any(k in text for k in keywords):
            return category

    return "uncategorized"