//+------------------------------------------------------------------+
//|                                              ForexMindAI_EA.mq5  |
//|                       ForexMind AI Trading Assistant MT5 EA      |
//|                       https://github.com/forexmind-ai            |
//+------------------------------------------------------------------+
#property copyright "ForexMind AI Team"
#property link      "https://github.com/forexmind-ai"
#property version   "3.50"
#property description "Automated MetaTrader 5 Execution EA for ForexMind AI"

#include <Trade\Trade.mqh>

// Inputs
input string   InpServerUrl    = "https://forexmind-ai-pro.onrender.com"; // ForexMind AI Server URL
input double   InpRiskPercent  = 1.0;                                     // Risk Per Trade (%)
input double   InpMinConf      = 55.0;                                    // Minimum AI Confidence (%)
input int      InpMagicNumber  = 424242;                                  // EA Magic Number
input int      InpPollInterval = 5;                                       // Poll Interval (Seconds)

// Global Objects
CTrade         m_trade;
string         m_last_signal    = "NONE";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   m_trade.SetExpertMagicNumber(InpMagicNumber);
   EventSetTimer(InpPollInterval);
   Print("⚡ ForexMind AI EA Active for Chart Symbol: ", Symbol(), " Account #", AccountInfoInteger(ACCOUNT_LOGIN));
   SendAccountPing();
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   Comment("");
}

//+------------------------------------------------------------------+
//| Timer event function                                             |
//+------------------------------------------------------------------+
void OnTimer()
{
   SendAccountPing();
   FetchAndExecuteSignal();
}

//+------------------------------------------------------------------+
//| Register account heartbeat status to server                      |
//+------------------------------------------------------------------+
void SendAccountPing()
{
   string pingUrl = InpServerUrl + "/api/mt5/ping";
   string headers = "Content-Type: application/json\r\n";
   string payload = StringFormat("{\"account_id\":\"%d\",\"broker\":\"%s\",\"balance\":%.2f,\"equity\":%.2f,\"leverage\":%d}",
                                 AccountInfoInteger(ACCOUNT_LOGIN),
                                 AccountInfoString(ACCOUNT_COMPANY),
                                 AccountInfoDouble(ACCOUNT_BALANCE),
                                 AccountInfoDouble(ACCOUNT_EQUITY),
                                 (int)AccountInfoInteger(ACCOUNT_LEVERAGE));
   
   char post_data[];
   char result[];
   string result_headers;
   
   StringToCharArray(payload, post_data, 0, StringLen(payload));
   WebRequest("POST", pingUrl, headers, 2000, post_data, result, result_headers);
}

//+------------------------------------------------------------------+
//| Fetch signal for THIS chart symbol and execute trade              |
//+------------------------------------------------------------------+
void FetchAndExecuteSignal()
{
   string currentSym = Symbol();
   // Normalize symbol name (e.g. EURUSD.r or EURUSD -> EURUSD)
   string cleanSym = currentSym;
   if (StringFind(cleanSym, "EUR") >= 0) cleanSym = "EURUSD";
   else if (StringFind(cleanSym, "GBP") >= 0) cleanSym = "GBPUSD";
   else if (StringFind(cleanSym, "JPY") >= 0) cleanSym = "USDJPY";
   else if (StringFind(cleanSym, "XAU") >= 0 || StringFind(cleanSym, "GOLD") >= 0) cleanSym = "XAUUSD";
   else if (StringFind(cleanSym, "AUD") >= 0) cleanSym = "AUDUSD";

   string sigUrl  = InpServerUrl + "/api/signal";
   string headers = "Content-Type: application/json\r\n";
   string payload = StringFormat("{\"symbol\":\"%s\",\"main_timeframe\":\"M15\",\"account_balance\":%.2f,\"risk_percent\":%.1f,\"min_confidence\":%.2f}",
                                 cleanSym, AccountInfoDouble(ACCOUNT_BALANCE), InpRiskPercent, InpMinConf / 100.0);
   
   char post_data[];
   char result[];
   string result_headers;
   
   StringToCharArray(payload, post_data, 0, StringLen(payload));

   int res = WebRequest("POST", sigUrl, headers, 3000, post_data, result, result_headers);

   if (res == 200)
   {
      string response_str = CharArrayToString(result);
      ProcessJsonResponse(response_str, currentSym);
   }
   else
   {
      Print("WebRequest failed. Code: ", res, ". Check URL in MT5 Tools -> Options -> Expert Advisors.");
   }
}

//+------------------------------------------------------------------+
//| Process signal and execute position                              |
//+------------------------------------------------------------------+
void ProcessJsonResponse(string json, string tradeSymbol)
{
   string signal = ExtractJsonValue(json, "final_signal");
   double confidence = StringToDouble(ExtractJsonValue(json, "confidence_pct"));
   double sl = StringToDouble(ExtractJsonValue(json, "stop_loss"));
   double tp = StringToDouble(ExtractJsonValue(json, "take_profit"));
   double lot = StringToDouble(ExtractJsonValue(json, "suggested_lot"));

   Comment(StringFormat("⚡ ForexMind AI Connected\nAccount #%d (%s)\nChart: %s | Signal: %s (%.1f%% Conf)\nSL: %.5f | TP: %.5f | Lot: %.2f",
                        AccountInfoInteger(ACCOUNT_LOGIN), AccountInfoString(ACCOUNT_COMPANY), tradeSymbol, signal, confidence, sl, tp, lot));

   // Execute Trade if signal is valid (BUY/SELL)
   if (signal == "BUY" || signal == "SELL")
   {
      if (confidence >= InpMinConf)
      {
         if (PositionsTotal() == 0)
         {
            if (signal == "BUY" && m_last_signal != "BUY")
            {
               Print("⚡ Executing BUY Order on ", tradeSymbol, " Lot: ", lot, " SL: ", sl, " TP: ", tp);
               m_trade.Buy(lot, tradeSymbol, 0, sl, tp, "ForexMind AI BUY");
               m_last_signal = "BUY";
            }
            else if (signal == "SELL" && m_last_signal != "SELL")
            {
               Print("⚡ Executing SELL Order on ", tradeSymbol, " Lot: ", lot, " SL: ", sl, " TP: ", tp);
               m_trade.Sell(lot, tradeSymbol, 0, sl, tp, "ForexMind AI SELL");
               m_last_signal = "SELL";
            }
         }
      }
      else
      {
         Print("Signal ", signal, " received for ", tradeSymbol, " (Conf ", confidence, "%), skipped below threshold ", InpMinConf, "%");
      }
   }
}

//+------------------------------------------------------------------+
//| Extract string value from simple JSON string                     |
//+------------------------------------------------------------------+
string ExtractJsonValue(string json, string key)
{
   string pattern = "\"" + key + "\":";
   int pos = StringFind(json, pattern);
   if (pos < 0) return "";
   
   int start = pos + StringLen(pattern);
   int end_comma = StringFind(json, ",", start);
   int end_brace = StringFind(json, "}", start);
   int end = (end_comma > 0 && end_comma < end_brace) ? end_comma : end_brace;
   
   string val = StringSubstr(json, start, end - start);
   StringReplace(val, "\"", "");
   StringTrimLeft(val);
   StringTrimRight(val);
   return val;
}
