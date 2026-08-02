import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/watchlist/data/backend_watchlist_item.dart';

void main() {
  group('BackendWatchlistItem', () {
    test('parses a valid backend entry', () {
      final item = BackendWatchlistItem.fromJson(const <String, dynamic>{
        'id': 4,
        'user_id': 7,
        'symbol': 'BTCUSDT',
        'exchange': 'BYBIT',
        'created_at': '2026-08-02T20:00:00Z',
      });

      expect(item.id, 4);
      expect(item.userId, 7);
      expect(item.symbol, 'BTCUSDT');
      expect(item.exchange, 'BYBIT');
      expect(item.baseAssetSymbol, 'BTC');
      expect(item.createdAt.isUtc, isTrue);
    });

    test('rejects an invalid backend entry', () {
      expect(
        () => BackendWatchlistItem.fromJson(const <String, dynamic>{
          'id': 0,
          'user_id': 7,
          'symbol': '',
          'exchange': 'BYBIT',
          'created_at': 'invalid',
        }),
        throwsFormatException,
      );
    });
  });

  group('WatchlistSymbolMapper', () {
    test('converts a CoinGecko symbol to USDT', () {
      expect(WatchlistSymbolMapper.toUsdtPair('btc'), 'BTCUSDT');
    });

    test('does not duplicate the quote asset', () {
      expect(WatchlistSymbolMapper.toUsdtPair('ethusdt'), 'ETHUSDT');
    });

    test('extracts the base asset', () {
      expect(WatchlistSymbolMapper.baseAssetFromPair('SOLUSDT'), 'SOL');
    });
  });
}
