import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/alerts/data/backend_price_alert.dart';
import 'package:p_trader_ai/features/alerts/providers/backend_price_alert_state.dart';

void main() {
  group('BackendPriceAlertState', () {
    test('starts empty and unloaded', () {
      const state = BackendPriceAlertState.initial();

      expect(state.alerts, isEmpty);
      expect(state.isLoading, isFalse);
      expect(state.isMutating, isFalse);
      expect(state.hasLoaded, isFalse);
      expect(state.errorMessage, isNull);
    });

    test('filters enabled and triggered alerts', () {
      final enabledTriggered = _alert(id: 1, isEnabled: true, triggered: true);
      final enabledPending = _alert(id: 2, isEnabled: true, triggered: false);
      final disabledTriggered = _alert(
        id: 3,
        isEnabled: false,
        triggered: true,
      );

      final state = BackendPriceAlertState(
        alerts: <BackendPriceAlert>[
          enabledTriggered,
          enabledPending,
          disabledTriggered,
        ],
        isLoading: false,
        isMutating: false,
        hasLoaded: true,
      );

      expect(state.enabledAlerts.map((alert) => alert.id), <int>[1, 2]);

      expect(state.triggeredAlerts.map((alert) => alert.id), <int>[1, 3]);
    });

    test('finds an alert by backend ID', () {
      final state = BackendPriceAlertState(
        alerts: <BackendPriceAlert>[_alert(id: 7), _alert(id: 8)],
        isLoading: false,
        isMutating: false,
        hasLoaded: true,
      );

      expect(state.findById(8)?.id, 8);
      expect(state.findById(99), isNull);
    });

    test('clears transient messages', () {
      final state = BackendPriceAlertState(
        alerts: const <BackendPriceAlert>[],
        isLoading: false,
        isMutating: false,
        hasLoaded: true,
        errorMessage: 'Load failed',
        infoMessage: 'Updated',
      );

      final cleared = state.copyWith(clearError: true, clearInfo: true);

      expect(cleared.errorMessage, isNull);
      expect(cleared.infoMessage, isNull);
      expect(cleared.hasLoaded, isTrue);
    });
  });
}

BackendPriceAlert _alert({
  required int id,
  bool isEnabled = true,
  bool triggered = false,
}) {
  return BackendPriceAlert(
    id: id,
    userId: 5,
    symbol: 'BTCUSDT',
    exchange: 'BYBIT',
    condition: BackendPriceAlertCondition.above,
    targetPrice: 120000,
    isEnabled: isEnabled,
    triggered: triggered,
    createdAt: DateTime.utc(2026, 8, 2),
  );
}
