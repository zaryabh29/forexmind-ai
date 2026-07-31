def generate_signal_explanation(
    signal: str,
    confidence: float,
    mtf_bias: int,
    rsi: float,
    ema_50_above_200: int,
    price_above_ema200: int,
    spread: float,
    atr: float,
    rr_ratio: float,
    is_news_blackout: bool,
    news_info: dict = None
):
    """
    Generates human-readable Explainable AI (XAI) rationale for Buy, Sell, or No Trade decisions.
    """
    reasons = []
    warnings = []

    # 1. Multi-Timeframe Alignment
    if mtf_bias == 1:
        reasons.append("Higher timeframes (H1 and H4) are strongly BULLISH.")
    elif mtf_bias == -1:
        reasons.append("Higher timeframes (H1 and H4) are strongly BEARISH.")
    else:
        warnings.append("Higher timeframes (H1 and H4) are conflicting or ranging.")

    # 2. Moving Average Alignment
    if ema_50_above_200 == 1 and price_above_ema200 == 1:
        reasons.append("Price is trading above both EMA 50 and EMA 200 (Bullish Trend Structure).")
    elif ema_50_above_200 == 0 and price_above_ema200 == 0:
        reasons.append("Price is trading below both EMA 50 and EMA 200 (Bearish Trend Structure).")
    else:
        warnings.append("Moving averages indicate price compression / pullback phase.")

    # 3. Momentum (RSI 14)
    if 45 <= rsi <= 65:
        reasons.append(f"RSI 14 is at {rsi:.1f}, showing healthy momentum without overbought/oversold risk.")
    elif rsi > 70:
        warnings.append(f"RSI 14 is overbought ({rsi:.1f}), increasing short-term reversal risk.")
    elif rsi < 30:
        warnings.append(f"RSI 14 is oversold ({rsi:.1f}), increasing bounce risk.")

    # 4. Volatility & Spread
    if atr > 0:
        spread_ratio = spread / atr
        if spread_ratio > 0.4:
            warnings.append(f"Spread ({spread:.5f}) is relatively high compared to current ATR ({atr:.5f}).")
        else:
            reasons.append("Spread is acceptable relative to market volatility.")

    # 5. Risk / Reward Ratio
    if rr_ratio >= 2.0:
        reasons.append(f"Risk/Reward ratio is valid at 1:{rr_ratio:.1f} (Minimum threshold: 1:2.0).")
    else:
        warnings.append(f"Risk/Reward ratio (1:{rr_ratio:.1f}) is below minimum target of 1:2.0.")

    # 6. News Events
    if is_news_blackout and news_info:
        warnings.append(f"HIGH IMPACT NEWS ALERT: '{news_info.get('event')}' nearby. Increased slippage risk.")

    # 7. Model Confidence
    conf_pct = round(confidence * 100, 1)
    if conf_pct >= 65.0:
        reasons.append(f"AI Machine Learning Model confidence is high at {conf_pct}%.")
    else:
        warnings.append(f"AI Machine Learning Model confidence ({conf_pct}%) is below strict threshold (65%).")

    # Synthesize Market Condition Summary
    if signal == "BUY":
        market_condition = "Bullish Confluence & Trend Continuation Setup"
    elif signal == "SELL":
        market_condition = "Bearish Confluence & Breakdown Setup"
    else:
        market_condition = "Unclear / Conflicting Market Structure (Filter Triggered)"

    return {
        "market_condition": market_condition,
        "reasons": reasons if reasons else ["No specific bullish/bearish confirmation."],
        "warnings": warnings if warnings else ["No major risk warnings detected."],
        "summary": f"Final Signal: {signal} with {conf_pct}% confidence. " +
                   ("Setup approved by Decision Engine." if signal != "NO TRADE" else "Trade rejected due to risk filters.")
    }
