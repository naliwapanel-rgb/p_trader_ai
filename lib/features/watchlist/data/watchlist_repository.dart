import '../../../core/services/local_storage_service.dart';

class WatchlistRepository {
  WatchlistRepository(this._localStorageService);

  final LocalStorageService _localStorageService;

  static const String _watchlistKey = 'watchlist_coin_ids';

  List<String> getWatchlistCoinIds() {
    return _localStorageService.getStringList(_watchlistKey);
  }

  Future<void> addCoin(String coinId) async {
    final currentIds = getWatchlistCoinIds();

    if (currentIds.contains(coinId)) {
      return;
    }

    final updatedIds = [...currentIds, coinId];
    await _localStorageService.setStringList(_watchlistKey, updatedIds);
  }

  Future<void> removeCoin(String coinId) async {
    final currentIds = getWatchlistCoinIds();

    final updatedIds = currentIds.where((id) => id != coinId).toList();
    await _localStorageService.setStringList(_watchlistKey, updatedIds);
  }

  bool isCoinInWatchlist(String coinId) {
    return getWatchlistCoinIds().contains(coinId);
  }

  Future<void> clearWatchlist() async {
    await _localStorageService.remove(_watchlistKey);
  }
}
