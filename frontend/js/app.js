document.addEventListener("DOMContentLoaded", () => {
    initApp();
});

async function initApp() {
    initThemeToggle();
    setupTabSwitching();
    await loadSymbolOptions();
    await checkConnectedAccounts();
    
    // Auto-refresh live candles & signal analysis every 4 seconds
    setInterval(updateSignalAnalysis, 4000);
    setInterval(checkConnectedAccounts, 10000);

    // Connect WebSocket Live Stream
    if (typeof marketWS !== "undefined") {
        marketWS.connect();
    }

    // Event Listeners
    const btnAnalyze = document.getElementById("btn-analyze");
    if (btnAnalyze) btnAnalyze.addEventListener("click", updateSignalAnalysis);

    const selectSymbol = document.getElementById("select-symbol");
    if (selectSymbol) selectSymbol.addEventListener("change", updateSignalAnalysis);

    const selectTimeframe = document.getElementById("select-timeframe");
    if (selectTimeframe) selectTimeframe.addEventListener("change", updateSignalAnalysis);

    const selectDir = document.getElementById("select-direction");
    if (selectDir) selectDir.addEventListener("change", updateSignalAnalysis);

    const btnBacktest = document.getElementById("btn-run-backtest");
    if (btnBacktest) btnBacktest.addEventListener("click", updateBacktest);

    const btnRisk = document.getElementById("btn-calc-risk");
    if (btnRisk) btnRisk.addEventListener("click", updateRiskCalc);

    const btnSendTg = document.getElementById("btn-send-tg");
    if (btnSendTg) btnSendTg.addEventListener("click", sendTelegramTestAlert);

    // Initial Signal Trigger
    await updateSignalAnalysis();
}

function initThemeToggle() {
    const btnToggle = document.getElementById("theme-toggle-btn");
    const savedTheme = localStorage.getItem("forexmind_theme") || "dark";
    
    document.documentElement.setAttribute("data-theme", savedTheme);
    if (btnToggle) btnToggle.textContent = savedTheme === "dark" ? "🌙 Dark" : "☀️ Light";

    if (btnToggle) {
        btnToggle.addEventListener("click", () => {
            const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
            const newTheme = currentTheme === "dark" ? "light" : "dark";
            
            document.documentElement.setAttribute("data-theme", newTheme);
            localStorage.setItem("forexmind_theme", newTheme);
            btnToggle.textContent = newTheme === "dark" ? "🌙 Dark" : "☀️ Light";
            
            updateSignalAnalysis();
        });
    }
}

function setupTabSwitching() {
    const allTabs = document.querySelectorAll(".tab-btn, .nav-item");
    
    allTabs.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetSec = btn.getAttribute("data-sec");

            allTabs.forEach(b => {
                if (b.getAttribute("data-sec") === targetSec) {
                    b.classList.add("active");
                } else {
                    b.classList.remove("active");
                }
            });

            document.querySelectorAll(".app-section").forEach(sec => {
                sec.classList.remove("active");
            });

            const activeSec = document.getElementById(targetSec);
            if (activeSec) {
                activeSec.classList.add("active");
            }

            if (targetSec === "sec-matrix") loadMTFMatrix();
            if (targetSec === "sec-backtest") updateBacktest();
            if (targetSec === "sec-news") loadSentimentRadar();
            if (targetSec === "sec-ea") {
                loadMQL5Code();
                checkConnectedAccounts();
            }
        });
    });
}

async function loadSymbolOptions() {
    try {
        const data = await API.getSymbols();
        const selectSymbol = document.getElementById("select-symbol");
        const selectSymbolRisk = document.getElementById("risk-symbol");

        if (selectSymbol && selectSymbol.options.length === 0) {
            data.symbols.forEach(sym => {
                const opt1 = document.createElement("option");
                opt1.value = sym;
                opt1.textContent = sym;
                selectSymbol.appendChild(opt1);
            });
        }

        if (selectSymbolRisk && selectSymbolRisk.options.length === 0) {
            data.symbols.forEach(sym => {
                const opt2 = document.createElement("option");
                opt2.value = sym;
                opt2.textContent = sym;
                selectSymbolRisk.appendChild(opt2);
            });
        }
    } catch (err) {
        console.error("Failed to load symbols:", err);
    }
}

async function checkConnectedAccounts() {
    try {
        const data = await API.getSymbols();
        const count = data.connected_count || 0;
        const accounts = data.connected_accounts || [];

        const badge = document.getElementById("accounts-count-badge");
        if (badge) {
            badge.textContent = `🔌 ${count} MT5 Active`;
            badge.className = count > 0 ? "badge-live online" : "badge-live offline";
        }

        const statusCount = document.getElementById("account-status-count");
        if (statusCount) {
            statusCount.textContent = `${count} Connected Account${count === 1 ? '' : 's'}`;
            statusCount.className = count > 0 ? "status-badge BUY" : "status-badge NEUTRAL";
        }

        const tbody = document.getElementById("mt5-accounts-table-body");
        if (tbody) {
            if (accounts.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align: center; color: var(--text-muted);">
                            No MT5 accounts connected yet. Download the EA below and add it to your MetaTrader 5 terminal.
                        </td>
                    </tr>
                `;
            } else {
                tbody.innerHTML = "";
                accounts.forEach(acc => {
                    const tr = document.createElement("tr");
                    tr.innerHTML = `
                        <td><strong>#${acc.account_id}</strong></td>
                        <td>${acc.broker}</td>
                        <td>$${acc.balance.toFixed(2)}</td>
                        <td>$${acc.equity.toFixed(2)}</td>
                        <td>1:${acc.leverage}</td>
                        <td><span class="status-badge ${acc.status === 'ONLINE' ? 'BUY' : 'SELL'}">${acc.status}</span></td>
                        <td>${acc.last_seen}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
        }
    } catch (err) {
        console.error("Error checking connected accounts:", err);
    }
}

async function updateSignalAnalysis() {
    const symbolEl = document.getElementById("select-symbol");
    const timeframeEl = document.getElementById("select-timeframe");
    const directionEl = document.getElementById("select-direction");
    const balanceEl = document.getElementById("input-balance");
    const riskEl = document.getElementById("input-risk");

    if (!symbolEl || !timeframeEl) return;

    const symbol = symbolEl.value || "EURUSD";
    const timeframe = timeframeEl.value || "M15";
    const direction = directionEl ? directionEl.value : "AUTO";
    const balance = balanceEl ? balanceEl.value : 1000;
    const risk = riskEl ? riskEl.value : 1.0;

    const container = document.getElementById("signal-card-container");
    if (!container) return;

    try {
        const res = await API.getSignal(symbol, timeframe, balance, risk, 0.55, false, direction);

        const sigBadge = document.getElementById("signal-badge");
        const sigTitle = document.getElementById("signal-title");
        const sigConf = document.getElementById("signal-confidence");

        if (sigBadge) sigBadge.className = `hero-header ${res.final_signal.replace(' ', '_')}`;
        if (sigTitle) sigTitle.textContent = res.final_signal;
        if (sigConf) sigConf.textContent = `AI Confidence: ${res.confidence_pct}% | Model Bias: ${res.raw_ml_signal}`;

        const elEntry = document.getElementById("val-entry");
        const elSl = document.getElementById("val-sl");
        const elTp = document.getElementById("val-tp");
        const elLot = document.getElementById("val-lot");
        const elRr = document.getElementById("val-rr");
        const elCond = document.getElementById("val-condition");

        if (elEntry) elEntry.textContent = res.entry_price;
        if (elSl) elSl.textContent = `${res.stop_loss} (${res.sl_pips}p)`;
        if (elTp) elTp.textContent = `${res.take_profit} (${res.tp_pips}p)`;
        if (elLot) elLot.textContent = `${res.suggested_lot} Lot`;
        if (elRr) elRr.textContent = res.risk_reward;
        if (elCond) elCond.textContent = res.market_condition;

        const reasonsList = document.getElementById("xai-reasons");
        const warningsList = document.getElementById("xai-warnings");

        if (reasonsList) {
            reasonsList.innerHTML = "";
            (res.reasons || []).forEach(r => {
                const li = document.createElement("li");
                li.textContent = r;
                reasonsList.appendChild(li);
            });
        }

        if (warningsList) {
            warningsList.innerHTML = "";
            (res.warnings || []).forEach(w => {
                const li = document.createElement("li");
                li.textContent = w;
                warningsList.appendChild(li);
            });
        }

        if (res.chart_candles && res.chart_candles.length > 0) {
            renderCandlestickChart("candlestick-chart", res.chart_candles);
        }

    } catch (err) {
        console.error("Error fetching signal:", err);
    }
}

async function loadMTFMatrix() {
    const symbolEl = document.getElementById("select-symbol");
    const symbol = symbolEl ? symbolEl.value : "EURUSD";
    try {
        const res = await API.getMTFMatrix(symbol);
        const tbody = document.getElementById("mtf-table-body");
        if (!tbody) return;
        tbody.innerHTML = "";

        (res.matrix || []).forEach(row => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><strong>${row.timeframe}</strong></td>
                <td>${row.close}</td>
                <td>${row.trend}</td>
                <td>${row.rsi}</td>
                <td><span class="status-badge ${row.state}">${row.state}</span></td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error("Error loading MTF matrix:", err);
    }
}

async function loadSentimentRadar() {
    const symbolEl = document.getElementById("select-symbol");
    const symbol = symbolEl ? symbolEl.value : "EURUSD";
    try {
        const res = await API.getSentiment(symbol);
        const labelEl = document.getElementById("sentiment-label");
        if (labelEl) labelEl.textContent = `${res.sentiment_label} (${res.sentiment_score})`;
        
        const listContainer = document.getElementById("sentiment-news-list");
        if (!listContainer) return;
        listContainer.innerHTML = "";
        
        const items = res.items || (res.news_feed ? res.news_feed.headlines : []);
        (items || []).forEach(item => {
            const headlineText = item.headline || item.title || "Market Update";
            const sentLabel = item.sentiment || "Neutral";
            
            const div = document.createElement("div");
            div.className = `level-card`;
            div.innerHTML = `
                <div style="font-size:12px; font-weight:600; margin-bottom:4px;">${headlineText}</div>
                <span class="status-badge ${sentLabel === 'Bullish' ? 'BUY' : (sentLabel === 'Bearish' ? 'SELL' : 'NEUTRAL')}">${sentLabel}</span>
            `;
            listContainer.appendChild(div);
        });
    } catch (err) {
        console.error("Error loading sentiment radar:", err);
    }
}

async function sendTelegramTestAlert() {
    const tokenEl = document.getElementById("tg-token");
    const chatEl = document.getElementById("tg-chat-id");
    const symbolEl = document.getElementById("select-symbol");
    const statusDiv = document.getElementById("tg-status");

    if (!tokenEl || !chatEl || !statusDiv) return;

    try {
        statusDiv.textContent = "Sending Telegram alert...";
        const res = await API.sendTelegramAlert(tokenEl.value, chatEl.value, symbolEl ? symbolEl.value : "EURUSD");
        if (res.status === "SUCCESS") {
            statusDiv.innerHTML = `<span style="color: var(--buy-color); font-weight: bold;">Telegram Signal Alert Sent Successfully!</span>`;
        } else {
            statusDiv.innerHTML = `<span style="color: var(--sell-color); font-weight: bold;">Failed: ${res.message || res.error}</span>`;
        }
    } catch (err) {
        statusDiv.textContent = "Telegram sending error.";
    }
}

async function loadMQL5Code() {
    try {
        const code = await API.getMQL5Script();
        const codeBox = document.getElementById("mql5-code-box");
        if (codeBox) codeBox.textContent = code;
    } catch (err) {
        console.error("Error loading MQL5 script:", err);
    }
}

async function updateBacktest() {
    const btnBacktest = document.getElementById("btn-run-backtest");
    const symbolEl = document.getElementById("select-symbol");
    const timeframeEl = document.getElementById("select-timeframe");

    const symbol = symbolEl ? symbolEl.value : "EURUSD";
    const timeframe = timeframeEl ? timeframeEl.value : "M15";

    const elNet = document.getElementById("bt-net-profit");
    const elWin = document.getElementById("bt-win-rate");
    const elPf = document.getElementById("bt-profit-factor");
    const elDd = document.getElementById("bt-max-dd");

    if (btnBacktest) {
        btnBacktest.disabled = true;
        btnBacktest.textContent = "⏳ Running Backtest...";
    }
    if (elNet) elNet.textContent = "Calculating...";
    if (elWin) elWin.textContent = "Calculating...";

    try {
        const res = await API.runBacktest(symbol, timeframe, 1000, 1.0, 0.55);
        const s = res.summary;

        if (elNet) elNet.textContent = `$${s.net_profit} (${s.net_return_pct}%)`;
        if (elWin) elWin.textContent = `${s.win_rate_pct}% (${s.win_count}W/${s.loss_count}L)`;
        if (elPf) elPf.textContent = s.profit_factor;
        if (elDd) elDd.textContent = `${s.max_drawdown_pct}%`;

        renderEquityChart("equity-chart", res.equity_curve);

        const tbody = document.getElementById("bt-trades-body");
        if (tbody) {
            tbody.innerHTML = "";
            (res.trades || []).slice(-15).forEach(t => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>#${t.trade_id}</td>
                    <td>${t.entry_time.split(' ')[1] || t.entry_time}</td>
                    <td><span class="status-badge ${t.signal}">${t.signal}</span></td>
                    <td>${t.entry_price}</td>
                    <td>${t.exit_price}</td>
                    <td style="color: ${t.pnl >= 0 ? 'var(--buy-color)' : 'var(--sell-color)'}; font-weight: bold;">
                        ${t.pnl >= 0 ? '+' : ''}$${t.pnl}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }

    } catch (err) {
        console.error("Error running backtest:", err);
    } finally {
        if (btnBacktest) {
            btnBacktest.disabled = false;
            btnBacktest.textContent = "Run Strategy Backtest";
        }
    }
}

async function updateRiskCalc() {
    const symbolEl = document.getElementById("risk-symbol");
    const balanceEl = document.getElementById("risk-balance");
    const riskEl = document.getElementById("risk-percent");
    const slPipsEl = document.getElementById("risk-sl-pips");

    const symbol = symbolEl ? symbolEl.value : "EURUSD";
    const balance = balanceEl ? balanceEl.value : 1000;
    const risk = riskEl ? riskEl.value : 1.0;
    const slPips = slPipsEl ? slPipsEl.value : 25;

    try {
        const res = await API.calculateRisk(balance, risk, slPips, symbol);
        const elLot = document.getElementById("res-risk-lot");
        const elUsd = document.getElementById("res-risk-usd");

        if (elLot) elLot.textContent = `${res.suggested_lot_size} Lot`;
        if (elUsd) elUsd.textContent = `$${res.risk_amount_usd}`;
    } catch (err) {
        console.error("Error calculating risk:", err);
    }
}
