import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/alerts/data/backend_price_alert.dart';

void main() {
  group('BackendPriceAlert', () {
    test('parses a backend price-above alert', () {
      final alert = BackendPriceAlert.fromJson(<String, dynamic>{
        'id': 11,
        'user_id': 7,
        'symbol': 'BTCUSDT',
        'exchange': 'BYBIT',
        'alert_type': 'PRICE_ABOVE',
        'target_value': 120000,
        'is_enabled': true,
        'triggered': false,
        'created_at': '2026-08-02T20:00:00Z',
      });

      expect(alert.id, 11);
      expect(alert.baseAssetSymbol, 'BTC');
      expect(alert.condition, BackendPriceAlertCondition.above);
      expect(alert.targetPrice, 120000);
      expect(alert.createdAt.isUtc, isTrue);
    });

    test('accepts legacy ABOVE and BELOW values', () {
      expect(
        BackendPriceAlertCondition.fromBackendValue('above'),
        BackendPriceAlertCondition.above,
      );

      expect(
        BackendPriceAlertCondition.fromBackendValue('BELOW'),
        BackendPriceAlertCondition.below,
      );
    });

    test('rejects invalid backend alert data', () {
      expect(
        () => BackendPriceAlert.fromJson(<String, dynamic>{
          'id': 0,
          'user_id': 7,
          'symbol': 'BTCUSDT',
          'exchange': 'BYBIT',
          'alert_type': 'PRICE_ABOVE',
          'target_value': -1,
          'is_enabled': true,
          'triggered': false,
          'created_at': 'invalid',
        }),
        throwsFormatException,
      );
    });

    test('normalizes symbols to USDT pairs', () {
      expect(PriceAlertSymbolMapper.toTradingPair(' btc '), 'BTCUSDT');

      expect(PriceAlertSymbolMapper.toTradingPair('eth/usdt'), 'ETHUSDT');

      expect(PriceAlertSymbolMapper.toBaseAssetSymbol('SOLUSDT'), 'SOL');
    });
  });
}
