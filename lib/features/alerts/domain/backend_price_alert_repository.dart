import '../data/backend_price_alert.dart';

abstract interface class BackendPriceAlertRepository {
  Future<List<BackendPriceAlert>> listAlerts();

  Future<BackendPriceAlert> getAlert(int alertId);

  Future<BackendPriceAlert> createAlert({
    required String symbol,
    required String exchange,
    required BackendPriceAlertCondition condition,
    required double targetPrice,
  });

  Future<BackendPriceAlert> updateAlert({
    required int alertId,
    String? symbol,
    String? exchange,
    BackendPriceAlertCondition? condition,
    double? targetPrice,
    bool? isEnabled,
    bool? triggered,
  });

  Future<void> deleteAlert(int alertId);
}
