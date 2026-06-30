import 'package:shared_preferences/shared_preferences.dart';

class WatchlistService {
  static const String _key = 'watchlist_coin_ids';

  Future<List<String>> getWatchlist() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getStringList(_key) ?? [];
  }

  Future<void> add(String coinId) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_key) ?? [];

    if (!list.contains(coinId)) {
      list.add(coinId);
      await prefs.setStringList(_key, list);
    }
  }

  Future<void> remove(String coinId) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_key) ?? [];

    list.remove(coinId);
    await prefs.setStringList(_key, list);
  }

  Future<bool> contains(String coinId) async {
    final prefs = await SharedPreferences.getInstance();
    final list = prefs.getStringList(_key) ?? [];

    return list.contains(coinId);
  }
}
