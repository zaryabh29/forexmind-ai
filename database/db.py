import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DB_DIR, "forexmind.db")

def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Table 1: Signals
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT NOT NULL,
        timeframe TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        final_signal TEXT NOT NULL,
        confidence REAL NOT NULL,
        entry_price REAL NOT NULL,
        stop_loss REAL NOT NULL,
        take_profit REAL NOT NULL,
        risk_reward TEXT NOT NULL,
        suggested_lot REAL NOT NULL,
        market_condition TEXT,
        reasons TEXT,
        warnings TEXT
    );
    """)

    # Table 2: Executed Trades (MT5 Sync)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mt5_ticket INTEGER UNIQUE,
        symbol TEXT NOT NULL,
        signal_type TEXT NOT NULL,
        lot_size REAL NOT NULL,
        open_price REAL NOT NULL,
        stop_loss REAL NOT NULL,
        take_profit REAL NOT NULL,
        close_price REAL,
        profit_loss REAL,
        open_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        close_time DATETIME,
        status TEXT DEFAULT 'OPEN'
    );
    """)

    # Table 3: Telegram Bot Subscribers
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telegram_subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT UNIQUE NOT NULL,
        username TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table 4: System Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        level TEXT NOT NULL,
        module TEXT NOT NULL,
        message TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()
    print("Database initialized successfully at:", DB_FILE)

def log_signal(signal_data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO signals (symbol, timeframe, final_signal, confidence, entry_price, stop_loss, take_profit, risk_reward, suggested_lot, market_condition, reasons, warnings)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal_data.get('symbol', 'EURUSD'),
        signal_data.get('timeframe', 'M15'),
        signal_data.get('final_signal', 'NO TRADE'),
        signal_data.get('confidence_pct', 0.0),
        signal_data.get('entry_price', 0.0),
        signal_data.get('stop_loss', 0.0),
        signal_data.get('take_profit', 0.0),
        signal_data.get('risk_reward', '1:2.0'),
        signal_data.get('suggested_lot', 0.01),
        signal_data.get('market_condition', ''),
        " | ".join(signal_data.get('reasons', [])),
        " | ".join(signal_data.get('warnings', []))
    ))
    conn.commit()
    conn.close()

def get_recent_signals(limit: int = 20):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM signals ORDER BY id DESC LIMIT {limit}", conn)
    conn.close()
    return df.to_dict(orient='records')

def get_db_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM signals")
    total_signals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM trades")
    total_trades = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM telegram_subscribers WHERE is_active = 1")
    total_subscribers = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_signals": total_signals,
        "total_trades": total_trades,
        "active_subscribers": total_subscribers
    }

if __name__ == "__main__":
    init_db()
