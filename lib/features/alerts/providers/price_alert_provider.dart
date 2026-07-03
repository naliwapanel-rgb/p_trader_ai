import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/local_storage_provider.dart';
import '../data/price_alert.dart';
import '../data/price_alert_repository.dart';

final priceAlertRepositoryProvider = Provider<PriceAlertRepository>((ref) {
  final localStorage = ref.watch(localStorageServiceProvider);
  return PriceAlertRepository(localStorage);
});

final priceAlertsProvider =
    NotifierProvider<PriceAlertNotifier, List<PriceAlert>>(
      PriceAlertNotifier.new,
    );

class PriceAlertNotifier extends Notifier<List<PriceAlert>> {
  late final PriceAlertRepository _repository;

  @override
  List<PriceAlert> build() {
    _repository = ref.watch(priceAlertRepositoryProvider);
    return _repository.getAlerts();
  }

  Future<void> addAlert(PriceAlert alert) async {
    await _repository.addAlert(alert);
    state = _repository.getAlerts();
  }

  Future<void> removeAlert(String id) async {
    await _repository.removeAlert(id);
    state = _repository.getAlerts();
  }

  Future<void> updateAlert(PriceAlert alert) async {
    await _repository.updateAlert(alert);
    state = _repository.getAlerts();
  }

  Future<void> clearAlerts() async {
    await _repository.clearAlerts();
    state = [];
  }
}
