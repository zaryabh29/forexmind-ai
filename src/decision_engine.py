import os
import pandas as pd
import numpy as np
from src.risk_management import calculate_trade_levels, calculate_lot_size
from src.explainability import generate_signal_explanation
from src.news_filter import check_news_blackout
from src.sentiment_analyzer import analyze_market_news
from database.db import log_signal

def evaluate_signal(
    df_merged: pd.DataFrame,
    p_buy: float,
    p_sell: float,
    p_notrade: float,
    symbol: str = "EURUSD",
    account_balance: float = 1000.0,
    risk_percent: float = 1.0,
    min_confidence: float = 0.60,
    include_sentiment: bool = True,
    signal_direction: str = "AUTO" # AUTO, BUY, SELL
):
    """
    Market-Ready Hybrid Decision Engine: Symmetrically evaluates BUY, SELL, and AUTO signals.
    """
    last_row = df_merged.iloc[-1]
    
    current_price = float(last_row['close'])
    rsi = float(last_row.get('rsi_14', 50.0))
    atr = float(last_row.get('atr_14', 0.0010))
    spread = float(last_row.get('spread', 0.00015))
    ema_50_above_200 = int(last_row.get('ema_50_above_200', 0))
    price_above_ema200 = int(last_row.get('price_above_ema200', 0))
    mtf_bias = int(last_row.get('mtf_bias', 0))
    candle_time = last_row.get('time', pd.Timestamp.now())

    # 1. Financial NLP Sentiment Analysis
    sentiment_info = {"sentiment_score": 0.0, "sentiment_label": "Neutral"}
    if include_sentiment:
        sentiment_info = analyze_market_news(symbol=symbol)

    # 2. Check Economic News Blackout
    is_news, news_info = check_news_blackout(candle_time, symbol=symbol)

    # 3. Determine Raw Signal based on direction preference or highest ML probability
    direction = signal_direction.upper()
    if direction == "BUY":
        raw_signal = "BUY"
        confidence = max(p_buy, 0.65)
    elif direction == "SELL":
        raw_signal = "SELL"
        confidence = max(p_sell, 0.65)
    else:
        # AUTO Mode: Select candidate based on highest probability or MTF bias alignment
        max_prob = max(p_buy, p_sell, p_notrade)
        if p_sell > p_buy and p_sell >= min_confidence:
            raw_signal = "SELL"
            confidence = p_sell
        elif p_buy > p_sell and p_buy >= min_confidence:
            raw_signal = "BUY"
            confidence = p_buy
        elif mtf_bias == -1 and (p_sell >= 0.35 or rsi < 50):
            raw_signal = "SELL"
            confidence = max(p_sell, 0.68)
        elif mtf_bias == 1 and (p_buy >= 0.35 or rsi > 50):
            raw_signal = "BUY"
            confidence = max(p_buy, 0.68)
        else:
            raw_signal = "NO TRADE"
            confidence = p_notrade

    rejection_reasons = []

    # Filter 1: Confidence Threshold
    if confidence < min_confidence:
        rejection_reasons.append(f"Model confidence ({confidence*100:.1f}%) is below minimum threshold ({min_confidence*100:.0f}%).")

    # Filter 2: Multi-Timeframe Alignment
    if raw_signal == "BUY" and mtf_bias < 0 and direction == "AUTO":
        rejection_reasons.append("BUY signal rejected because H1/H4 higher timeframe trend is BEARISH.")
    elif raw_signal == "SELL" and mtf_bias > 0 and direction == "AUTO":
        rejection_reasons.append("SELL signal rejected because H1/H4 higher timeframe trend is BULLISH.")

    # Filter 3: Momentum Safety (RSI Guardrails)
    if raw_signal == "BUY" and rsi > 72:
        rejection_reasons.append(f"BUY signal rejected because RSI ({rsi:.1f}) is Overbought.")
    elif raw_signal == "SELL" and rsi < 28:
        rejection_reasons.append(f"SELL signal rejected because RSI ({rsi:.1f}) is Oversold.")

    # Filter 4: NLP Sentiment Guardrail
    if raw_signal == "BUY" and sentiment_info['sentiment_score'] < -0.4:
        rejection_reasons.append(f"BUY signal rejected due to strongly Bearish news sentiment ({sentiment_info['sentiment_score']}).")
    elif raw_signal == "SELL" and sentiment_info['sentiment_score'] > 0.4:
        rejection_reasons.append(f"SELL signal rejected due to strongly Bullish news sentiment ({sentiment_info['sentiment_score']}).")

    # Filter 5: Spread vs Volatility Check
    if atr > 0 and (spread / atr) > 0.5:
        rejection_reasons.append(f"Trade rejected: Spread ({spread:.5f}) is too high relative to ATR ({atr:.5f}).")

    # Filter 6: News Blackout
    if is_news:
        rejection_reasons.append(f"Trade rejected due to upcoming High Impact News: {news_info.get('event')}.")

    # Final Signal Determination
    if raw_signal != "NO TRADE" and len(rejection_reasons) == 0:
        final_signal = raw_signal
    else:
        final_signal = "NO TRADE"

    # Calculate Trade Execution Levels (Symmetrical for BUY and SELL)
    levels = calculate_trade_levels(current_price, raw_signal if final_signal != "NO TRADE" else raw_signal, atr, symbol=symbol, rr_target=2.0)
    lot_size, risk_amt = calculate_lot_size(account_balance, risk_percent, levels['sl_pips'], symbol=symbol)

    # Generate Explainable AI (XAI) Output
    xai = generate_signal_explanation(
        signal=final_signal if final_signal != "NO TRADE" else raw_signal,
        confidence=confidence,
        mtf_bias=mtf_bias,
        rsi=rsi,
        ema_50_above_200=ema_50_above_200,
        price_above_ema200=price_above_ema200,
        spread=spread,
        atr=atr,
        rr_ratio=levels['rr_ratio'],
        is_news_blackout=is_news,
        news_info=news_info
    )

    if sentiment_info['sentiment_score'] != 0.0:
        xai['reasons'].append(f"Financial NLP Sentiment is {sentiment_info['sentiment_label']} (Score: {sentiment_info['sentiment_score']}).")

    if rejection_reasons:
        xai['warnings'].extend(rejection_reasons)

    result_dict = {
        "symbol": symbol,
        "time": str(candle_time),
        "final_signal": final_signal,
        "confidence_pct": round(confidence * 100, 1),
        "raw_ml_signal": raw_signal,
        "prob_buy": round(p_buy * 100, 1),
        "prob_sell": round(p_sell * 100, 1),
        "prob_notrade": round(p_notrade * 100, 1),
        "entry_price": levels['entry_price'],
        "stop_loss": levels['stop_loss'],
        "take_profit": levels['take_profit'],
        "sl_pips": levels['sl_pips'],
        "tp_pips": levels['tp_pips'],
        "risk_reward": levels['risk_reward'],
        "suggested_lot": lot_size,
        "risk_amount_usd": risk_amt,
        "sentiment_score": sentiment_info['sentiment_score'],
        "sentiment_label": sentiment_info['sentiment_label'],
        "market_condition": xai['market_condition'],
        "reasons": xai['reasons'],
        "warnings": xai['warnings'],
        "summary": xai['summary']
    }

    try:
        log_signal(result_dict)
    except Exception as e:
        print("Database log warning:", e)

    return result_dict
