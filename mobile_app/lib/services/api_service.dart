import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Use 10.0.2.2 for Android emulator or 127.0.0.1 for iOS simulator/desktop
  static const String baseUrl = 'http://10.0.2.2:8000';

  static Future<Map<String, dynamic>> fetchSymbols() async {
    final response = await http.get(Uri.parse('$baseUrl/api/symbols'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to load symbols');
  }

  static Future<Map<String, dynamic>> fetchTradingSignal({
    required String symbol,
    required String timeframe,
    required double balance,
    required double riskPercent,
    required String direction,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/signal'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'symbol': symbol,
        'main_timeframe': timeframe,
        'account_balance': balance,
        'risk_percent': riskPercent,
        'min_confidence': 0.55,
        'use_ensemble': false,
        'signal_direction': direction,
      }),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to fetch trading signal');
  }

  static Future<Map<String, dynamic>> fetchMtfMatrix(String symbol) async {
    final response = await http.get(Uri.parse('$baseUrl/api/mtf-matrix?symbol=$symbol'));
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to fetch MTF matrix');
  }

  static Future<Map<String, dynamic>> runBacktest({
    required String symbol,
    required String timeframe,
    required double balance,
    required double riskPercent,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/backtest'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'symbol': symbol,
        'main_timeframe': timeframe,
        'initial_balance': balance,
        'risk_percent': riskPercent,
        'min_confidence': 0.55,
      }),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to run backtest');
  }
}
