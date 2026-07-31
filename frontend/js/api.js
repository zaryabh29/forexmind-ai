const API_BASE = ""; // Relative URL for FastAPI server

const API = {
    async getSymbols() {
        const res = await fetch(`${API_BASE}/api/symbols`);
        return await res.json();
    },

    async getSignal(symbol, mainTimeframe, accountBalance, riskPercent, minConfidence, useEnsemble = false, signalDirection = "AUTO") {
        const res = await fetch(`${API_BASE}/api/signal`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: symbol,
                main_timeframe: mainTimeframe,
                account_balance: parseFloat(accountBalance),
                risk_percent: parseFloat(riskPercent),
                min_confidence: parseFloat(minConfidence),
                use_ensemble: useEnsemble,
                signal_direction: signalDirection
            })
        });
        return await res.json();
    },

    async getMTFMatrix(symbol) {
        const res = await fetch(`${API_BASE}/api/mtf-matrix?symbol=${symbol}`);
        return await res.json();
    },

    async runBacktest(symbol, mainTimeframe, initialBalance, riskPercent, minConfidence) {
        const res = await fetch(`${API_BASE}/api/backtest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: symbol,
                main_timeframe: mainTimeframe,
                initial_balance: parseFloat(initialBalance),
                risk_percent: parseFloat(riskPercent),
                min_confidence: parseFloat(minConfidence)
            })
        });
        return await res.json();
    },

    async calculateRisk(accountBalance, riskPercent, slPips, symbol) {
        const res = await fetch(`${API_BASE}/api/calculate-risk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                account_balance: parseFloat(accountBalance),
                risk_percent: parseFloat(riskPercent),
                sl_pips: parseFloat(slPips),
                symbol: symbol
            })
        });
        return await res.json();
    },

    async trainModel(symbol, modelType) {
        const res = await fetch(`${API_BASE}/api/models/train`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                symbol: symbol,
                model_type: modelType
            })
        });
        return await res.json();
    },

    async getSentiment(symbol) {
        const res = await fetch(`${API_BASE}/api/sentiment?symbol=${symbol}`);
        return await res.json();
    },

    async sendTelegramAlert(botToken, chatId, symbol) {
        const res = await fetch(`${API_BASE}/api/telegram/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                bot_token: botToken,
                chat_id: chatId,
                symbol: symbol
            })
        });
        return await res.json();
    },

    async getDatabaseSignals() {
        const res = await fetch(`${API_BASE}/api/database/signals`);
        return await res.json();
    },

    async getMQL5Script() {
        const res = await fetch(`${API_BASE}/api/mql5/download`);
        return await res.text();
    }
};
