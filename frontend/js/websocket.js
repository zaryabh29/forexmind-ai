class MarketWebSocket {
    constructor() {
        this.socket = null;
        this.reconnectTimer = null;
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host || '127.0.0.1:8000';
        const wsUrl = `${protocol}//${host}/ws/stream`;

        try {
            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = () => {
                console.log("WebSocket connected to ForexMind AI Live Stream.");
                this.updateStatusBadge(true);
            };

            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.event === "tick") {
                    this.onLiveTick(data);
                }
            };

            this.socket.onclose = () => {
                console.warn("WebSocket disconnected. Reconnecting in 5s...");
                this.updateStatusBadge(false);
                this.scheduleReconnect();
            };

            this.socket.onerror = (err) => {
                console.error("WebSocket error:", err);
                this.updateStatusBadge(false);
            };

        } catch (e) {
            console.error("WebSocket initialization failed:", e);
            this.updateStatusBadge(false);
        }
    }

    scheduleReconnect() {
        if (!this.reconnectTimer) {
            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                this.connect();
            }, 5000);
        }
    }

    updateStatusBadge(isConnected) {
        const badge = document.getElementById("ws-status-badge");
        if (badge) {
            if (isConnected) {
                badge.className = "ws-badge online";
                badge.textContent = "📡 LIVE STREAM";
            } else {
                badge.className = "ws-badge offline";
                badge.textContent = "🔌 DISCONNECTED";
            }
        }
    }

    onLiveTick(data) {
        // Pulse live ticker indicator
        const ticker = document.getElementById("live-ticker");
        if (ticker) {
            ticker.style.opacity = "1.0";
            setTimeout(() => { ticker.style.opacity = "0.7"; }, 500);
        }
    }
}

const marketWS = new MarketWebSocket();
