import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'services/api_service.dart';

void main() {
  runApp(const ForexMindApp());
}

class ForexMindApp extends StatefulWidget {
  const ForexMindApp({super.key});

  @override
  State<ForexMindApp> createState() => _ForexMindAppState();
}

class _ForexMindAppState extends State<ForexMindApp> {
  ThemeMode _themeMode = ThemeMode.dark;

  void toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ForexMind AI Pro',
      debugShowCheckedModeBanner: false,
      themeMode: _themeMode,
      
      // Light Theme
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: const Color(0xFFF8FAFC),
        primaryColor: const Color(0xFF2563EB),
        cardColor: Colors.white,
        textTheme: GoogleFonts.interTextTheme(ThemeData.light().textTheme),
        colorScheme: const ColorScheme.light(
          primary: Color(0xFF2563EB),
          surface: Colors.white,
        ),
      ),

      // Dark Theme
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        primaryColor: const Color(0xFF3B82F6),
        cardColor: const Color(0xFF1E293B),
        textTheme: GoogleFonts.interTextTheme(ThemeData.dark().textTheme),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF3B82F6),
          surface: Color(0xFF1E293B),
        ),
      ),

      home: MainNavigationScreen(
        onToggleTheme: toggleTheme,
        isDarkMode: _themeMode == ThemeMode.dark,
      ),
    );
  }
}

class MainNavigationScreen extends StatefulWidget {
  final VoidCallback onToggleTheme;
  final bool isDarkMode;

  const MainNavigationScreen({
    super.key,
    required this.onToggleTheme,
    required this.isDarkMode,
  });

  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _selectedIndex = 0;
  String _selectedSymbol = "EURUSD";
  String _selectedTimeframe = "M15";
  String _selectedDirection = "AUTO";

  Map<String, dynamic>? _signalData;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _fetchSignal();
  }

  Future<void> _fetchSignal() async {
    setState(() => _isLoading = true);
    try {
      final res = await ApiService.fetchTradingSignal(
        symbol: _selectedSymbol,
        timeframe: _selectedTimeframe,
        balance: 1000.0,
        riskPercent: 1.0,
        direction: _selectedDirection,
      );
      setState(() {
        _signalData = res;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = widget.isDarkMode;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: Theme.of(context).cardColor,
        elevation: 0.5,
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: Theme.of(context).primaryColor,
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text('FX', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
            ),
            const SizedBox(width: 10),
            Text('ForexMind AI PRO', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: isDark ? Colors.white : Colors.black)),
          ],
        ),
        actions: [
          IconButton(
            icon: Icon(isDark ? Icons.light_mode : Icons.dark_mode),
            onPressed: widget.onToggleTheme,
            tooltip: 'Toggle Theme Mode',
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Controls Bar
                  Card(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: Row(
                        children: [
                          Expanded(
                            child: DropdownButton<String>(
                              value: _selectedSymbol,
                              isExpanded: true,
                              underline: const SizedBox(),
                              items: ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "AUDUSD"]
                                  .map((s) => DropdownMenuItem(value: s, child: Text(s)))
                                  .toList(),
                              onChanged: (val) {
                                if (val != null) {
                                  setState(() => _selectedSymbol = val);
                                  _fetchSignal();
                                }
                              },
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: DropdownButton<String>(
                              value: _selectedDirection,
                              isExpanded: true,
                              underline: const SizedBox(),
                              items: ["AUTO", "BUY", "SELL"]
                                  .map((d) => DropdownMenuItem(value: d, child: Text(d)))
                                  .toList(),
                              onChanged: (val) {
                                if (val != null) {
                                  setState(() => _selectedDirection = val);
                                  _fetchSignal();
                                }
                              },
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Signal Card Display
                  if (_signalData != null) _buildSignalCard(_signalData!),
                ],
              ),
            ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        type: BottomNavigationBarType.fixed,
        onTap: (index) => setState(() => _selectedIndex = index),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.show_chart), label: 'Signals'),
          BottomNavigationBarItem(icon: Icon(Icons.grid_on), label: 'Matrix'),
          BottomNavigationBarItem(icon: Icon(Icons.calculate), label: 'Risk'),
          BottomNavigationBarItem(icon: Icon(Icons.bar_chart), label: 'Backtest'),
        ],
      ),
    );
  }

  Widget _buildSignalCard(Map<String, dynamic> sig) {
    final String signalType = sig['final_signal'] ?? 'NO TRADE';
    final Color badgeColor = signalType == 'BUY'
        ? const Color(0xFF10B981)
        : (signalType == 'SELL' ? const Color(0xFFEF4444) : const Color(0xFFF59E0B));

    return Card(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(20.0),
        child: Column(
          children: [
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 16),
              decoration: BoxDecoration(
                color: badgeColor.withOpacity(0.15),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: badgeColor),
              ),
              child: Column(
                children: [
                  Text(
                    signalType,
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.extrabold, color: badgeColor),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'AI Confidence: ${sig['confidence_pct']}%',
                    style: const TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _paramRow('Entry Price', '${sig['entry_price']}'),
            _paramRow('Stop Loss (SL)', '${sig['stop_loss']} (${sig['sl_pips']} pips)', color: Colors.red),
            _paramRow('Take Profit (TP)', '${sig['take_profit']} (${sig['tp_pips']} pips)', color: Colors.green),
            _paramRow('Risk / Reward', '${sig['risk_reward']}'),
            _paramRow('Suggested Lot', '${sig['suggested_lot']} Lot'),
          ],
        ),
      ),
    );
  }

  Widget _paramRow(String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
          Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: color)),
        ],
      ),
    );
  }
}
