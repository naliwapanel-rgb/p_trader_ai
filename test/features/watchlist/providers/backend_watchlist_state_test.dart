import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/watchlist/data/backend_watchlist_item.dart';
import 'package:p_trader_ai/features/watchlist/providers/backend_watchlist_state.dart';

void main() {
  group('BackendWatchlistState helpers', () {
    test('filters items by normalized exchange', () {
      final state = _state();

      final items = state.itemsForExchange(' bybit ');

      expect(items, hasLength(2));
      expect(
        items.map((item) => item.symbol),
        containsAll(<String>['BTCUSDT', 'ETHUSDT']),
      );
    });

    test('returns base asset symbols', () {
      final state = _state();

      expect(state.baseAssetSymbolsForExchange('BYBIT'), <String>{
        'BTC',
        'ETH',
      });
    });

    test('matches a CoinGecko asset symbol', () {
      final state = _state();

      expect(
        state.containsAssetSymbol(assetSymbol: 'btc', exchange: 'bybit'),
        isTrue,
      );

      expect(
        state.containsAssetSymbol(assetSymbol: 'sol', exchange: 'bybit'),
        isFalse,
      );
    });

    test('counts only the requested exchange', () {
      final state = _state();

      expect(state.countForExchange('BYBIT'), 2);

      expect(state.countForExchange('BINANCE'), 1);
    });
  });
}

BackendWatchlistState _state() {
  return BackendWatchlistState(
    items: <BackendWatchlistItem>[
      _item(id: 1, symbol: 'BTCUSDT', exchange: 'BYBIT'),
      _item(id: 2, symbol: 'ETHUSDT', exchange: 'BYBIT'),
      _item(id: 3, symbol: 'SOLUSDT', exchange: 'BINANCE'),
    ],
    isLoading: false,
    isMutating: false,
    hasLoaded: true,
  );
}

BackendWatchlistItem _item({
  required int id,
  required String symbol,
  required String exchange,
}) {
  return BackendWatchlistItem(
    id: id,
    userId: 7,
    symbol: symbol,
    exchange: exchange,
    createdAt: DateTime.utc(2026, 8, 2),
  );
}
