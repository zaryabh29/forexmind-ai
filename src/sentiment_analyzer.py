import re

BULLISH_KEYWORDS = [
    'rate hike', 'hawkish', 'gdp growth', 'inflation surge', 'strong employment',
    'bullish', 'breakout', 'record high', 'stimulus', 'gold rally', 'payrolls beat',
    'expansion', 'optimism', 'positive outlook', 'rate increase'
]

BEARISH_KEYWORDS = [
    'rate cut', 'dovish', 'recession', 'unemployment rise', 'inflation drop',
    'bearish', 'breakdown', 'crash', 'economic decline', 'payrolls miss',
    'contraction', 'fear', 'negative outlook', 'rate reduction', 'default risk'
]

def analyze_headline_sentiment(headline: str) -> float:
    """
    Computes a sentiment score between -1.0 (Bearish) and +1.0 (Bullish) for a headline.
    """
    text = headline.lower()
    score = 0.0

    for word in BULLISH_KEYWORDS:
        if word in text:
            score += 0.25

    for word in BEARISH_KEYWORDS:
        if word in text:
            score -= 0.25

    return max(-1.0, min(1.0, score))

def analyze_market_news(symbol: str = "EURUSD", headlines: list = None):
    """
    Aggregates sentiment scores across financial headlines for a target currency pair or Gold.
    """
    if headlines is None or len(headlines) == 0:
        headlines = [
            "Federal Reserve signals hawkish stance amid persistent inflation",
            "US Dollar index rebounds as non-farm payrolls exceed expectations",
            "Gold surges as geopolitical safe-haven demand increases",
            "European Central Bank debates potential rate cuts following weak PMI data",
            "Bank of Japan maintains accommodative monetary policy stance"
        ]

    curr1 = symbol[:3]
    curr2 = symbol[3:] if len(symbol) >= 6 else ""

    relevant_scores = []
    analyzed_items = []

    for item in headlines:
        score = analyze_headline_sentiment(item)
        
        # Check currency relevance
        is_relevant = False
        if curr1 in item or curr2 in item:
            is_relevant = True
        elif symbol == "XAUUSD" and ("gold" in item.lower() or "fed" in item.lower() or "usd" in item.lower()):
            is_relevant = True
        elif curr1 in ["EUR", "GBP", "USD", "JPY", "AUD"]:
            is_relevant = True

        if is_relevant:
            relevant_scores.append(score)
            analyzed_items.append({
                "headline": item,
                "score": score,
                "sentiment": "Bullish" if score > 0.1 else ("Bearish" if score < -0.1 else "Neutral")
            })

    avg_score = float(sum(relevant_scores) / len(relevant_scores)) if relevant_scores else 0.0
    sentiment_label = "Bullish" if avg_score > 0.1 else ("Bearish" if avg_score < -0.1 else "Neutral")

    return {
        "symbol": symbol,
        "sentiment_score": round(avg_score, 2),
        "sentiment_label": sentiment_label,
        "analyzed_count": len(analyzed_items),
        "items": analyzed_items
    }
