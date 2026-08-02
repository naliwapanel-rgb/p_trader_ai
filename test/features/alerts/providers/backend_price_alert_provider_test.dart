import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/alerts/data/backend_price_alert.dart';
import 'package:p_trader_ai/features/alerts/domain/backend_price_alert_repository.dart';
import 'package:p_trader_ai/features/alerts/providers/backend_price_alert_provider.dart';

void main() {
  group('BackendPriceAlertNotifier', () {
    test('loads authenticated backend alerts', () async {
      final repository = _FakePriceAlertRepository(
        alerts: <BackendPriceAlert>[_alert(id: 1)],
      );
      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(backendPriceAlertProvider.notifier).loadAlerts();

      final state = container.read(backendPriceAlertProvider);

      expect(repository.listCalls, 1);
      expect(state.alerts, hasLength(1));
      expect(state.hasLoaded, isTrue);
      expect(state.errorMessage, isNull);
    });

    test('creates and stores a backend alert', () async {
      final repository = _FakePriceAlertRepository();
      final container = _container(repository);
      addTearDown(container.dispose);

      final created = await container
          .read(backendPriceAlertProvider.notifier)
          .createAlert(
            symbol: 'BTC',
            condition: BackendPriceAlertCondition.above,
            targetPrice: 120000,
          );

      final state = container.read(backendPriceAlertProvider);

      expect(created?.symbol, 'BTCUSDT');
      expect(repository.createCalls, 1);
      expect(state.alerts, hasLength(1));
      expect(state.infoMessage, 'Price alert created.');
    });

    test('toggles enabled state through update', () async {
      final repository = _FakePriceAlertRepository(
        alerts: <BackendPriceAlert>[_alert(id: 4, isEnabled: true)],
      );
      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(backendPriceAlertProvider.notifier);

      await notifier.loadAlerts();
      final updated = await notifier.toggleEnabled(4);

      expect(updated?.isEnabled, isFalse);
      expect(repository.updateCalls, 1);
      expect(
        container.read(backendPriceAlertProvider).findById(4)?.isEnabled,
        isFalse,
      );
    });

    test('treats missing delete as idempotent', () async {
      final repository = _FakePriceAlertRepository(
        alerts: <BackendPriceAlert>[_alert(id: 7)],
      );
      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(backendPriceAlertProvider.notifier);

      await notifier.loadAlerts();

      repository.deleteError = const AppException(
        'Alert not found',
        statusCode: 404,
      );

      final deleted = await notifier.deleteAlert(7);
      final state = container.read(backendPriceAlertProvider);

      expect(deleted, isTrue);
      expect(state.alerts, isEmpty);
      expect(state.infoMessage, 'Price alert was already deleted.');
      expect(state.errorMessage, isNull);
    });

    test('stores repository load errors', () async {
      final repository = _FakePriceAlertRepository(
        listError: const AppException('Unable to load alerts'),
      );
      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(backendPriceAlertProvider.notifier).loadAlerts();

      final state = container.read(backendPriceAlertProvider);

      expect(state.errorMessage, 'Unable to load alerts');
      expect(state.isLoading, isFalse);
    });
  });
}

ProviderContainer _container(BackendPriceAlertRepository repository) {
  return ProviderContainer(
    overrides: [
      backendPriceAlertRepositoryProvider.overrideWithValue(repository),
    ],
  );
}

BackendPriceAlert _alert({
  required int id,
  bool isEnabled = true,
  bool triggered = false,
}) {
  return BackendPriceAlert(
    id: id,
    userId: 7,
    symbol: 'BTCUSDT',
    exchange: 'BYBIT',
    condition: BackendPriceAlertCondition.above,
    targetPrice: 120000,
    isEnabled: isEnabled,
    triggered: triggered,
    createdAt: DateTime.utc(2026, 8, 2, 20),
  );
}

class _FakePriceAlertRepository implements BackendPriceAlertRepository {
  _FakePriceAlertRepository({
    List<BackendPriceAlert> alerts = const <BackendPriceAlert>[],
    this.listError,
  }) : alerts = List<BackendPriceAlert>.of(alerts);

  List<BackendPriceAlert> alerts;
  final AppException? listError;
  AppException? deleteError;

  int listCalls = 0;
  int createCalls = 0;
  int updateCalls = 0;
  int deleteCalls = 0;

  @override
  Future<List<BackendPriceAlert>> listAlerts() async {
    listCalls += 1;

    final error = listError;

    if (error != null) {
      throw error;
    }

    return List<BackendPriceAlert>.of(alerts);
  }

  @override
  Future<BackendPriceAlert> getAlert(int alertId) async {
    return alerts.firstWhere((alert) => alert.id == alertId);
  }

  @override
  Future<BackendPriceAlert> createAlert({
    required String symbol,
    required String exchange,
    required BackendPriceAlertCondition condition,
    required double targetPrice,
  }) async {
    createCalls += 1;

    final alert = BackendPriceAlert(
      id: alerts.length + 1,
      userId: 7,
      symbol: PriceAlertSymbolMapper.toTradingPair(symbol),
      exchange: exchange.trim().toUpperCase(),
      condition: condition,
      targetPrice: targetPrice,
      isEnabled: true,
      triggered: false,
      createdAt: DateTime.utc(2026, 8, 2, 21),
    );

    alerts = <BackendPriceAlert>[...alerts, alert];

    return alert;
  }

  @override
  Future<BackendPriceAlert> updateAlert({
    required int alertId,
    String? symbol,
    String? exchange,
    BackendPriceAlertCondition? condition,
    double? targetPrice,
    bool? isEnabled,
    bool? triggered,
  }) async {
    updateCalls += 1;

    final index = alerts.indexWhere((alert) => alert.id == alertId);

    if (index == -1) {
      throw const AppException('Alert not found', statusCode: 404);
    }

    final current = alerts[index];

    final updated = current.copyWith(
      symbol: symbol == null
          ? null
          : PriceAlertSymbolMapper.toTradingPair(symbol),
      exchange: exchange?.trim().toUpperCase(),
      condition: condition,
      targetPrice: targetPrice,
      isEnabled: isEnabled,
      triggered: triggered,
    );

    alerts = List<BackendPriceAlert>.of(alerts);
    alerts[index] = updated;

    return updated;
  }

  @override
  Future<void> deleteAlert(int alertId) async {
    deleteCalls += 1;

    final error = deleteError;

    if (error != null) {
      throw error;
    }

    alerts = alerts
        .where((alert) => alert.id != alertId)
        .toList(growable: false);
  }
}
