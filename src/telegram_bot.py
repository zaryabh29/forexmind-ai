import json
import urllib.request
from database.db import get_db_connection

DEFAULT_BOT_TOKEN = "7000000000:AAFg_SampleForexMindBotToken" # Placeholder for user token

def format_telegram_message(signal_data: dict) -> str:
    sig = signal_data.get('final_signal', 'NO TRADE')
    emoji = "🟢" if sig == "BUY" else ("🔴" if sig == "SELL" else "🟡")
    
    msg = f"{emoji} <b>FOREXMIND AI SIGNAL ALERT</b> {emoji}\n\n"
    msg += f"<b>Instrument:</b> {signal_data.get('symbol', 'EURUSD')}\n"
    msg += f"<b>Signal:</b> {sig}\n"
    msg += f"<b>AI Confidence:</b> {signal_data.get('confidence_pct', 0.0)}%\n\n"
    
    if sig != "NO TRADE":
        msg += f"🎯 <b>Entry Price:</b> {signal_data.get('entry_price')}\n"
        msg += f"🛑 <b>Stop Loss:</b> {signal_data.get('stop_loss')} ({signal_data.get('sl_pips')} pips)\n"
        msg += f"💰 <b>Take Profit:</b> {signal_data.get('take_profit')} ({signal_data.get('tp_pips')} pips)\n"
        msg += f"⚖️ <b>Risk/Reward:</b> {signal_data.get('risk_reward')}\n"
        msg += f"📊 <b>Suggested Lot Size:</b> {signal_data.get('suggested_lot')} Lot\n\n"
    
    msg += f"💡 <b>Market Condition:</b> {signal_data.get('market_condition')}\n\n"
    
    reasons = signal_data.get('reasons', [])
    if reasons:
        msg += "<b>Confirmations:</b>\n"
        for r in reasons[:3]:
            msg += f"• {r}\n"
        msg += "\n"
        
    warnings = signal_data.get('warnings', [])
    if warnings:
        msg += "⚠️ <b>Risk Guardrails:</b>\n"
        for w in warnings[:2]:
            msg += f"• {w}\n"
            
    return msg

def send_telegram_alert(bot_token: str, chat_id: str, signal_data: dict):
    """
    Sends formatted HTML signal card alert to Telegram via Bot API.
    """
    if not bot_token or bot_token == DEFAULT_BOT_TOKEN:
        return {"status": "SKIPPED", "message": "Bot token not configured."}

    text = format_telegram_message(signal_data)
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }).encode('utf-8')

    try:
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
        res = urllib.request.urlopen(req)
        return {"status": "SUCCESS", "response": json.loads(res.read().decode('utf-8'))}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}

def broadcast_signal_to_subscribers(bot_token: str, signal_data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM telegram_subscribers WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        res = send_telegram_alert(bot_token, r['chat_id'], signal_data)
        results.append(res)
    return results
