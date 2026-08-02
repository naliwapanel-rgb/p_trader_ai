import '../domain/backend_price_alert_repository.dart';
import 'backend_price_alert.dart';
import 'price_alert_remote_data_source.dart';

class BackendPriceAlertRepositoryImpl implements BackendPriceAlertRepository {
  const BackendPriceAlertRepositoryImpl({
    required PriceAlertRemoteDataSource remoteDataSource,
  }) : _remoteDataSource = remoteDataSource;

  final PriceAlertRemoteDataSource _remoteDataSource;

  @override
  Future<List<BackendPriceAlert>> listAlerts() {
    return _remoteDataSource.listAlerts();
  }

  @override
  Future<BackendPriceAlert> getAlert(int alertId) {
    return _remoteDataSource.getAlert(alertId);
  }

  @override
  Future<BackendPriceAlert> createAlert({
    required String symbol,
    required String exchange,
    required BackendPriceAlertCondition condition,
    required double targetPrice,
  }) {
    return _remoteDataSource.createAlert(
      symbol: symbol,
      exchange: exchange,
      condition: condition,
      targetPrice: targetPrice,
    );
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
  }) {
    return _remoteDataSource.updateAlert(
      alertId: alertId,
      symbol: symbol,
      exchange: exchange,
      condition: condition,
      targetPrice: targetPrice,
      isEnabled: isEnabled,
      triggered: triggered,
    );
  }

  @override
  Future<void> deleteAlert(int alertId) {
    return _remoteDataSource.deleteAlert(alertId);
  }
}
