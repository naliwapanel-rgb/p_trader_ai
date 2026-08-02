import '../domain/watchlist_repository.dart';
import 'backend_watchlist_item.dart';
import 'watchlist_remote_data_source.dart';

class WatchlistRepositoryImpl implements WatchlistRepository {
  const WatchlistRepositoryImpl({
    required WatchlistRemoteDataSource remoteDataSource,
  }) : _remoteDataSource = remoteDataSource;

  final WatchlistRemoteDataSource _remoteDataSource;

  @override
  Future<List<BackendWatchlistItem>> listItems() {
    return _remoteDataSource.listItems();
  }

  @override
  Future<BackendWatchlistItem> createItem({
    required String symbol,
    required String exchange,
  }) {
    return _remoteDataSource.createItem(symbol: symbol, exchange: exchange);
  }

  @override
  Future<void> deleteItem(int itemId) {
    return _remoteDataSource.deleteItem(itemId);
  }
}
