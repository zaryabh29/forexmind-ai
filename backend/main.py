import os
import sys
import pandas as pd
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from data.generator import generate_all_datasets, SYMBOLS_CONFIG
from src.preprocessing import clean_data
from src.indicators import calculate_indicators
from src.multi_timeframe import align_multi_timeframe
from src.labeling import create_target_labels
from src.model_trainer import train_model, predict_signal, MODELS_DIR
from src.deep_learning import train_ensemble_model
from src.decision_engine import evaluate_signal
from src.risk_management import calculate_lot_size, calculate_trade_levels
from src.backtester import run_backtest
from src.news_filter import check_news_blackout
from src.sentiment_analyzer import analyze_market_news
from src.news_scraper import fetch_live_financial_news
from src.mt5_bridge import mt5_bridge
from src.broker_manager import broker_router
from src.saas_auth import register_user, authenticate_user
from src.telegram_bot import send_telegram_alert, broadcast_signal_to_subscribers
from database.db import init_db, get_recent_signals, get_db_stats
from backend.websocket_server import ws_manager
import joblib

app = FastAPI(
    title="ForexMind AI Pro - Institutional Quantitative Platform",
    description="Multi-Timeframe AI Signal System, MT5 Execution EA, Deep Learning & BUY/SELL Signal Engine",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
MQL5_DIR = os.path.join(PROJECT_ROOT, "mql5")

@app.on_event("startup")
def startup_event():
    init_db()
    eurusd_path = os.path.join(DATA_DIR, "EURUSD_M15.csv")
    if not os.path.exists(eurusd_path):
        print("Generating initial market datasets...")
        generate_all_datasets()

# Pydantic Schemas
class SignalRequest(BaseModel):
    symbol: str = "EURUSD"
    main_timeframe: str = "M15"
    account_balance: float = 1000.0
    risk_percent: float = 1.0
    min_confidence: float = 0.55
    use_ensemble: bool = False
    signal_direction: str = "AUTO"

class RiskCalcRequest(BaseModel):
    account_balance: float = 1000.0
    risk_percent: float = 1.0
    sl_pips: float = 25.0
    symbol: str = "EURUSD"

class BacktestRequest(BaseModel):
    symbol: str = "EURUSD"
    main_timeframe: str = "M15"
    initial_balance: float = 1000.0
    risk_percent: float = 1.0
    min_confidence: float = 0.55

class TrainModelRequest(BaseModel):
    symbol: str = "EURUSD"
    model_type: str = "random_forest"

class TelegramAlertRequest(BaseModel):
    bot_token: str
    chat_id: str
    symbol: str = "EURUSD"

class MT5ExecuteRequest(BaseModel):
    symbol: str = "EURUSD"
    signal_type: str = "BUY"
    lot_size: float = 0.01
    stop_loss: float = 0.0
    take_profit: float = 0.0

class MT5PingRequest(BaseModel):
    account_id: str
    broker: str = "MT5 Broker"
    balance: float = 1000.0
    equity: float = 1000.0
    leverage: int = 100

class AuthRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

# --- REST API Endpoints ---

@app.get("/api/symbols")
def get_symbols():
    accounts = mt5_bridge.get_connected_accounts()
    return {
        "symbols": list(SYMBOLS_CONFIG.keys()),
        "timeframes": ["M5", "M15", "H1", "H4"],
        "directions": ["AUTO", "BUY", "SELL"],
        "config": SYMBOLS_CONFIG,
        "db_stats": get_db_stats(),
        "mt5_status": mt5_bridge.get_account_info(),
        "connected_accounts": accounts,
        "connected_count": len([a for a in accounts if a["status"] == "ONLINE"])
    }

@app.post("/api/mt5/ping")
def ping_mt5_account(req: MT5PingRequest):
    mt5_bridge.register_account_ping(
        account_id=req.account_id,
        broker=req.broker,
        balance=req.balance,
        equity=req.equity,
        leverage=req.leverage
    )
    accounts = mt5_bridge.get_connected_accounts()
    return {
        "status": "REGISTERED",
        "account_id": req.account_id,
        "connected_accounts": accounts,
        "connected_count": len([a for a in accounts if a["status"] == "ONLINE"])
    }

@app.post("/api/signal")
def get_trading_signal(req: SignalRequest):
    symbol = req.symbol.upper()
    tf = req.main_timeframe.upper()

    file_tf = os.path.join(DATA_DIR, f"{symbol}_{tf}.csv")
    file_h1 = os.path.join(DATA_DIR, f"{symbol}_H1.csv")
    file_h4 = os.path.join(DATA_DIR, f"{symbol}_H4.csv")

    if not os.path.exists(file_tf):
        generate_all_datasets()

    df_lower = calculate_indicators(clean_data(pd.read_csv(file_tf)))
    df_h1 = calculate_indicators(clean_data(pd.read_csv(file_h1)))
    df_h4 = calculate_indicators(clean_data(pd.read_csv(file_h4)))

    df_merged = align_multi_timeframe(df_lower, df_h1, df_h4)

    model_suffix = "_ensemble_model.joblib" if req.use_ensemble else "_model.joblib"
    model_file = os.path.join(MODELS_DIR, f"{symbol}{model_suffix}")
    
    if not os.path.exists(model_file):
        df_labeled = create_target_labels(df_merged)
        if req.use_ensemble:
            _, _ = train_ensemble_model(df_labeled, symbol=symbol)
        else:
            _, _ = train_model(df_labeled, model_type="random_forest", symbol=symbol)

    model_dict = joblib.load(model_file)
    p_buy, p_sell, p_notrade = predict_signal(model_dict, df_merged)

    signal_res = evaluate_signal(
        df_merged,
        p_buy, p_sell, p_notrade,
        symbol=symbol,
        account_balance=req.account_balance,
        risk_percent=req.risk_percent,
        min_confidence=req.min_confidence,
        signal_direction=req.signal_direction
    )

    chart_candles = df_merged[['time', 'open', 'high', 'low', 'close', 'tick_volume']].tail(60).to_dict(orient='records')
    for c in chart_candles:
        c['time'] = str(c['time'])

    signal_res['chart_candles'] = chart_candles
    return signal_res

@app.get("/api/mtf-matrix")
def get_mtf_matrix(symbol: str = "EURUSD"):
    symbol = symbol.upper()
    matrix = []
    
    for tf in ["M5", "M15", "H1", "H4"]:
        f_path = os.path.join(DATA_DIR, f"{symbol}_{tf}.csv")
        if not os.path.exists(f_path):
            continue
        df = calculate_indicators(clean_data(pd.read_csv(f_path)))
        last = df.iloc[-1]
        
        rsi = float(last.get('rsi_14', 50.0))
        close = float(last.get('close', 0))
        ema_200 = float(last.get('ema_200', 0))
        
        trend = "Bullish" if close > ema_200 else "Bearish"
        state = "BUY" if (close > ema_200 and rsi > 50) else ("SELL" if (close < ema_200 and rsi < 50) else "NEUTRAL")
        
        matrix.append({
            "timeframe": tf,
            "close": close,
            "trend": trend,
            "rsi": round(rsi, 1),
            "ema_status": "Above EMA 200" if close > ema_200 else "Below EMA 200",
            "state": state
        })
        
    return {"symbol": symbol, "matrix": matrix}

@app.post("/api/backtest")
def run_backtest_api(req: BacktestRequest):
    symbol = req.symbol.upper()
    tf = req.main_timeframe.upper()

    file_tf = os.path.join(DATA_DIR, f"{symbol}_{tf}.csv")
    file_h1 = os.path.join(DATA_DIR, f"{symbol}_H1.csv")
    file_h4 = os.path.join(DATA_DIR, f"{symbol}_H4.csv")

    df_lower = calculate_indicators(clean_data(pd.read_csv(file_tf)))
    df_h1 = calculate_indicators(clean_data(pd.read_csv(file_h1)))
    df_h4 = calculate_indicators(clean_data(pd.read_csv(file_h4)))

    df_merged = align_multi_timeframe(df_lower, df_h1, df_h4)
    return run_backtest(
        df_merged,
        initial_balance=req.initial_balance,
        risk_percent=req.risk_percent,
        symbol=symbol,
        min_confidence=req.min_confidence
    )

@app.post("/api/calculate-risk")
def calculate_risk_api(req: RiskCalcRequest):
    lot_size, risk_amount = calculate_lot_size(
        account_balance=req.account_balance,
        risk_percent=req.risk_percent,
        sl_pips=req.sl_pips,
        symbol=req.symbol.upper()
    )
    return {
        "symbol": req.symbol,
        "account_balance": req.account_balance,
        "risk_percent": req.risk_percent,
        "risk_amount_usd": risk_amount,
        "sl_pips": req.sl_pips,
        "suggested_lot_size": lot_size
    }

@app.post("/api/models/train")
def train_model_api(req: TrainModelRequest):
    symbol = req.symbol.upper()
    file_tf = os.path.join(DATA_DIR, f"{symbol}_M15.csv")
    file_h1 = os.path.join(DATA_DIR, f"{symbol}_H1.csv")
    file_h4 = os.path.join(DATA_DIR, f"{symbol}_H4.csv")

    df_lower = calculate_indicators(clean_data(pd.read_csv(file_tf)))
    df_h1 = calculate_indicators(clean_data(pd.read_csv(file_h1)))
    df_h4 = calculate_indicators(clean_data(pd.read_csv(file_h4)))

    df_merged = align_multi_timeframe(df_lower, df_h1, df_h4)
    df_labeled = create_target_labels(df_merged)

    if req.model_type == "ensemble":
        metrics, _ = train_ensemble_model(df_labeled, symbol=symbol)
    else:
        metrics, _ = train_model(df_labeled, model_type=req.model_type, symbol=symbol)

    return metrics

@app.get("/api/sentiment")
def get_sentiment(symbol: str = "EURUSD"):
    news_feed = fetch_live_financial_news(symbol=symbol.upper())
    sentiment = analyze_market_news(symbol=symbol.upper())
    sentiment["news_feed"] = news_feed
    return sentiment

@app.post("/api/auth/register")
def auth_register(req: AuthRequest):
    return register_user(req.username, req.email or f"{req.username}@forexmind.ai", req.password)

@app.post("/api/auth/login")
def auth_login(req: AuthRequest):
    return authenticate_user(req.username, req.password)

@app.post("/api/telegram/send")
def send_telegram_signal(req: TelegramAlertRequest):
    sig_res = get_trading_signal(SignalRequest(symbol=req.symbol))
    return send_telegram_alert(req.bot_token, req.chat_id, sig_res)

@app.post("/api/mt5/execute")
def execute_mt5_order(req: MT5ExecuteRequest):
    return broker_router.execute_order(
        symbol=req.symbol,
        signal_type=req.signal_type,
        lot_size=req.lot_size,
        stop_loss=req.stop_loss,
        take_profit=req.take_profit
    )

@app.get("/api/database/signals")
def get_db_signal_history(limit: int = 20):
    return {"signals": get_recent_signals(limit=limit)}

@app.get("/api/mql5/download")
def download_mql5_ea():
    ea_file = os.path.join(MQL5_DIR, "ForexMindAI_EA.mq5")
    if os.path.exists(ea_file):
        with open(ea_file, "r") as f:
            return PlainTextResponse(f.read(), media_type="text/plain")
    raise HTTPException(status_code=404, detail="EA script not found.")

@app.get("/manifest.json")
def serve_manifest():
    m_path = os.path.join(FRONTEND_DIR, "manifest.json")
    if os.path.exists(m_path):
        return FileResponse(m_path, media_type="application/json")
    raise HTTPException(status_code=404, detail="Manifest not found.")

@app.get("/sw.js")
def serve_sw():
    sw_path = os.path.join(FRONTEND_DIR, "sw.js")
    if os.path.exists(sw_path):
        return FileResponse(sw_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Service worker not found.")

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            await ws_manager.broadcast({"event": "tick", "message": "Live market stream active"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

# Mount Static Frontend
os.makedirs(FRONTEND_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "ForexMind AI REST API v4.0 is running."}
