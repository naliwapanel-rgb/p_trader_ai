import '../data/backend_watchlist_item.dart';

abstract interface class WatchlistRepository {
  Future<List<BackendWatchlistItem>> listItems();

  Future<BackendWatchlistItem> createItem({
    required String symbol,
    required String exchange,
  });

  Future<void> deleteItem(int itemId);
}
