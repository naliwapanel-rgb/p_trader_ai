import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../../domain/entities/crypto_asset.dart';

class MarketCacheService {
  MarketCacheService(this._prefs);

  final SharedPreferences _prefs;

  List<CryptoAsset>? _cachedMarkets;
  DateTime? _lastFetchTime;

  static const String _marketsKey = 'cached_markets';
  static const String _lastFetchKey = 'cached_markets_last_fetch';

  static const Duration cacheDuration = Duration(seconds: 30);

  bool get hasValidCache {
    if (_cachedMarkets == null || _lastFetchTime == null) {
      _loadFromStorage();
    }

    if (_cachedMarkets == null || _lastFetchTime == null) {
      return false;
    }

    final age = DateTime.now().difference(_lastFetchTime!);
    return age < cacheDuration;
  }

  bool get hasCache {
    if (_cachedMarkets == null) {
      _loadFromStorage();
    }

    return _cachedMarkets != null && _cachedMarkets!.isNotEmpty;
  }

  List<CryptoAsset>? get cachedMarkets {
    if (_cachedMarkets == null) {
      _loadFromStorage();
    }

    return _cachedMarkets;
  }

  DateTime? get lastFetchTime {
    if (_lastFetchTime == null) {
      _loadFromStorage();
    }

    return _lastFetchTime;
  }

  Duration? get cacheAge {
    final lastFetch = lastFetchTime;

    if (lastFetch == null) {
      return null;
    }

    return DateTime.now().difference(lastFetch);
  }

  void saveMarkets(List<CryptoAsset> markets) {
    _cachedMarkets = markets;
    _lastFetchTime = DateTime.now();

    final encodedMarkets = markets
        .map((market) => jsonEncode(market.toJson()))
        .toList();

    _prefs.setStringList(_marketsKey, encodedMarkets);
    _prefs.setString(_lastFetchKey, _lastFetchTime!.toIso8601String());
  }

  void clear() {
    _cachedMarkets = null;
    _lastFetchTime = null;

    _prefs.remove(_marketsKey);
    _prefs.remove(_lastFetchKey);
  }

  void _loadFromStorage() {
    final rawMarkets = _prefs.getStringList(_marketsKey);
    final rawLastFetch = _prefs.getString(_lastFetchKey);

    if (rawMarkets == null || rawLastFetch == null) {
      return;
    }

    _cachedMarkets = rawMarkets
        .map((raw) => CryptoAsset.fromJson(jsonDecode(raw)))
        .toList();

    _lastFetchTime = DateTime.tryParse(rawLastFetch);
  }
}
