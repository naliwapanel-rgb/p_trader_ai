import 'dart:convert';

import '../../../core/services/local_storage_service.dart';
import 'price_alert.dart';

class PriceAlertRepository {
  PriceAlertRepository(this._localStorage);

  final LocalStorageService _localStorage;

  static const _alertsKey = 'price_alerts';

  List<PriceAlert> getAlerts() {
    final rawAlerts = _localStorage.getStringList(_alertsKey);

    return rawAlerts
        .map((raw) => PriceAlert.fromJson(jsonDecode(raw)))
        .toList();
  }

  Future<void> saveAlerts(List<PriceAlert> alerts) async {
    final encoded = alerts.map((alert) => jsonEncode(alert.toJson())).toList();

    await _localStorage.setStringList(_alertsKey, encoded);
  }

  Future<void> addAlert(PriceAlert alert) async {
    final alerts = getAlerts();
    alerts.add(alert);
    await saveAlerts(alerts);
  }

  Future<void> removeAlert(String id) async {
    final alerts = getAlerts().where((alert) => alert.id != id).toList();

    await saveAlerts(alerts);
  }

  Future<void> updateAlert(PriceAlert updatedAlert) async {
    final alerts = getAlerts();

    final index = alerts.indexWhere((alert) => alert.id == updatedAlert.id);

    if (index == -1) return;

    alerts[index] = updatedAlert;

    await saveAlerts(alerts);
  }

  Future<void> clearAlerts() async {
    await _localStorage.remove(_alertsKey);
  }
}
