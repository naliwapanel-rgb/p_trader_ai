import '../../domain/entities/crypto_asset.dart';

class MarketCacheService {
  List<CryptoAsset>? _cachedMarkets;
  DateTime? _lastFetchTime;

  static const Duration cacheDuration = Duration(seconds: 30);

  bool get hasValidCache {
    if (_cachedMarkets == null || _lastFetchTime == null) {
      return false;
    }

    final now = DateTime.now();
    final age = now.difference(_lastFetchTime!);

    return age < cacheDuration;
  }

  List<CryptoAsset>? get cachedMarkets => _cachedMarkets;

  void saveMarkets(List<CryptoAsset> markets) {
    _cachedMarkets = markets;
    _lastFetchTime = DateTime.now();
  }

  void clear() {
    _cachedMarkets = null;
    _lastFetchTime = null;
  }
}
