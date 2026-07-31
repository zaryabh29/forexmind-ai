//+------------------------------------------------------------------+
//|                                              ForexMindAI_EA.mq5  |
//|                       ForexMind AI Trading Assistant MT5 EA      |
//|                       https://github.com/forexmind-ai            |
//+------------------------------------------------------------------+
#property copyright "ForexMind AI Team"
#property link      "https://github.com/forexmind-ai"
#property version   "2.00"
#property description "Automated MetaTrader 5 Execution EA & Account Status Monitor for ForexMind AI"

#include <Trade\Trade.mqh>

// Inputs
input string   InpServerUrl    = "http://127.0.0.1:8000";             // ForexMind AI Server URL
input double   InpRiskPercent  = 1.0;                                // Risk Per Trade (%)
input double   InpMinConf      = 65.0;                               // Minimum AI Confidence (%)
input int      InpMagicNumber  = 424242;                             // EA Magic Number
input int      InpPollInterval = 10;                                 // Poll Interval (Seconds)

// Global Objects
CTrade         m_trade;
datetime       m_last_poll_time = 0;
string         m_last_signal    = "NONE";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   m_trade.SetExpertMagicNumber(InpMagicNumber);
   EventSetTimer(InpPollInterval);
   Print("ForexMind AI EA Initialized successfully for ", Symbol(), " Account #", AccountInfoInteger(ACCOUNT_LOGIN));
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
//| Fetch signal from API and execute on MT5 terminal                 |
//+------------------------------------------------------------------+
void FetchAndExecuteSignal()
{
   string sigUrl  = InpServerUrl + "/api/signal";
   string headers = "Content-Type: application/json\r\n";
   string payload = StringFormat("{\"symbol\":\"%s\",\"main_timeframe\":\"M15\",\"account_balance\":%.2f,\"risk_percent\":%.1f,\"min_confidence\":%.2f}",
                                 Symbol(), AccountInfoDouble(ACCOUNT_BALANCE), InpRiskPercent, InpMinConf / 100.0);
   
   char post_data[];
   char result[];
   string result_headers;
   
   StringToCharArray(payload, post_data, 0, StringLen(payload));

   int res = WebRequest("POST", sigUrl, headers, 3000, post_data, result, result_headers);

   if (res == 200)
   {
      string response_str = CharArrayToString(result);
      ProcessJsonResponse(response_str);
   }
   else
   {
      Print("WebRequest failed. Error code: ", res, ". Verify WebRequest URL permission in MT5 Options.");
   }
}

//+------------------------------------------------------------------+
//| Simple JSON parser & trade execution                              |
//+------------------------------------------------------------------+
void ProcessJsonResponse(string json)
{
   string signal = ExtractJsonValue(json, "final_signal");
   double confidence = StringToDouble(ExtractJsonValue(json, "confidence_pct"));
   double sl = StringToDouble(ExtractJsonValue(json, "stop_loss"));
   double tp = StringToDouble(ExtractJsonValue(json, "take_profit"));
   double lot = StringToDouble(ExtractJsonValue(json, "suggested_lot"));

   Comment(StringFormat("⚡ ForexMind AI Connected\nAccount #%d (%s)\nSymbol: %s | Signal: %s (%.1f%% Conf)\nSL: %.5f | TP: %.5f | Lot: %.2f",
                        AccountInfoInteger(ACCOUNT_LOGIN), AccountInfoString(ACCOUNT_COMPANY), Symbol(), signal, confidence, sl, tp, lot));

   // Execute Trade if signal is valid and no open position exists
   if (PositionsTotal() == 0 && confidence >= InpMinConf)
   {
      if (signal == "BUY" && m_last_signal != "BUY")
      {
         Print("Executing BUY order for ", Symbol(), " Lot: ", lot);
         m_trade.Buy(lot, Symbol(), 0, sl, tp, "ForexMind AI BUY");
         m_last_signal = "BUY";
      }
      else if (signal == "SELL" && m_last_signal != "SELL")
      {
         Print("Executing SELL order for ", Symbol(), " Lot: ", lot);
         m_trade.Sell(lot, Symbol(), 0, sl, tp, "ForexMind AI SELL");
         m_last_signal = "SELL";
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
