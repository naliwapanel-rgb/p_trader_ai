import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/watchlist/data/backend_watchlist_item.dart';
import 'package:p_trader_ai/features/watchlist/domain/watchlist_repository.dart';
import 'package:p_trader_ai/features/watchlist/providers/backend_watchlist_provider.dart';

void main() {
  group('BackendWatchlistNotifier', () {
    test('loads authenticated watchlist items', () async {
      final repository = _FakeWatchlistRepository(
        items: <BackendWatchlistItem>[_item(id: 1, symbol: 'BTCUSDT')],
      );

      final container = ProviderContainer(
        overrides: [
          backendWatchlistRepositoryProvider.overrideWithValue(repository),
        ],
      );

      addTearDown(container.dispose);

      await container.read(backendWatchlistProvider.notifier).loadItems();

      final state = container.read(backendWatchlistProvider);

      expect(repository.listCalls, 1);
      expect(state.hasLoaded, isTrue);
      expect(state.items, hasLength(1));
      expect(state.items.single.baseAssetSymbol, 'BTC');
    });

    test('creates a normalized Bybit item', () async {
      final repository = _FakeWatchlistRepository();

      final container = ProviderContainer(
        overrides: [
          backendWatchlistRepositoryProvider.overrideWithValue(repository),
        ],
      );

      addTearDown(container.dispose);

      final item = await container
          .read(backendWatchlistProvider.notifier)
          .createItem(assetSymbol: 'eth');

      expect(item?.symbol, 'ETHUSDT');
      expect(repository.createdSymbol, 'ETHUSDT');
      expect(repository.createdExchange, 'BYBIT');
      expect(container.read(backendWatchlistProvider).items, hasLength(1));
    });

    test('deletes an existing item', () async {
      final repository = _FakeWatchlistRepository(
        items: <BackendWatchlistItem>[_item(id: 3, symbol: 'SOLUSDT')],
      );

      final container = ProviderContainer(
        overrides: [
          backendWatchlistRepositoryProvider.overrideWithValue(repository),
        ],
      );

      addTearDown(container.dispose);

      final notifier = container.read(backendWatchlistProvider.notifier);

      await notifier.loadItems();

      final deleted = await notifier.deleteItem(3);

      expect(deleted, isTrue);
      expect(repository.deletedItemId, 3);
      expect(container.read(backendWatchlistProvider).items, isEmpty);
    });

    test('recovers an existing item after duplicate conflict', () async {
      final existing = _item(id: 8, symbol: 'BTCUSDT');

      final repository = _FakeWatchlistRepository(
        items: <BackendWatchlistItem>[existing],
        createError: const AppException(
          'Symbol already exists in watchlist',
          statusCode: 409,
        ),
      );

      final container = ProviderContainer(
        overrides: [
          backendWatchlistRepositoryProvider.overrideWithValue(repository),
        ],
      );

      addTearDown(container.dispose);

      final item = await container
          .read(backendWatchlistProvider.notifier)
          .createItem(assetSymbol: 'btc');

      expect(item?.id, 8);
      expect(repository.listCalls, 1);
      expect(container.read(backendWatchlistProvider).errorMessage, isNull);
    });
  });
}

class _FakeWatchlistRepository implements WatchlistRepository {
  _FakeWatchlistRepository({
    List<BackendWatchlistItem>? items,
    this.createError,
  }) : items = items ?? <BackendWatchlistItem>[];

  final List<BackendWatchlistItem> items;
  final AppException? createError;

  int listCalls = 0;
  String? createdSymbol;
  String? createdExchange;
  int? deletedItemId;

  @override
  Future<List<BackendWatchlistItem>> listItems() async {
    listCalls += 1;

    return List<BackendWatchlistItem>.from(items);
  }

  @override
  Future<BackendWatchlistItem> createItem({
    required String symbol,
    required String exchange,
  }) async {
    final error = createError;

    if (error != null) {
      throw error;
    }

    createdSymbol = symbol;
    createdExchange = exchange;

    final item = _item(
      id: items.length + 1,
      symbol: symbol,
      exchange: exchange,
    );

    items.add(item);

    return item;
  }

  @override
  Future<void> deleteItem(int itemId) async {
    deletedItemId = itemId;

    items.removeWhere((item) => item.id == itemId);
  }
}

BackendWatchlistItem _item({
  required int id,
  required String symbol,
  String exchange = 'BYBIT',
}) {
  return BackendWatchlistItem(
    id: id,
    userId: 7,
    symbol: symbol,
    exchange: exchange,
    createdAt: DateTime.utc(2026, 8, 2),
  );
}
