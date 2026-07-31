import json
import asyncio
import random
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    """
    Manages active WebSocket connections for live market & signal streaming.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.ticker_task = None
        self.prices = {
            "EURUSD": 1.0615,
            "GBPUSD": 1.2750,
            "USDJPY": 155.50,
            "XAUUSD": 2380.00,
            "AUDUSD": 0.6650
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebSocket client connected. Total active: {len(self.active_connections)}")
        
        if self.ticker_task is None or self.ticker_task.done():
            self.ticker_task = asyncio.create_task(self.start_live_tick_broadcaster())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("WebSocket client disconnected.")

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                pass

    async def start_live_tick_broadcaster(self):
        print("Starting live market tick broadcaster...")
        while len(self.active_connections) > 0:
            for symbol in self.prices:
                delta = random.choice([-1, 1]) * random.uniform(0.0001, 0.0004) if "USDJPY" not in symbol and "XAUUSD" not in symbol else random.choice([-1, 1]) * random.uniform(0.05, 0.25)
                self.prices[symbol] = round(self.prices[symbol] + delta, 5 if "USDJPY" not in symbol and "XAUUSD" not in symbol else 2)
            
            await self.broadcast({
                "event": "tick",
                "prices": self.prices,
                "timestamp": asyncio.get_event_loop().time()
            })
            await asyncio.sleep(2.0)

ws_manager = ConnectionManager()
