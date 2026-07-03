import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../providers/market_providers.dart';
import '../data/price_alert.dart';
import '../domain/price_alert_engine.dart';
import 'price_alert_provider.dart';

final triggeredAlertsProvider = Provider<List<PriceAlert>>((ref) {
  final alerts = ref.watch(priceAlertsProvider);
  final marketsAsync = ref.watch(liveMarketsProvider);

  final markets = marketsAsync.value ?? [];

  return alerts.where((alert) {
    if (!alert.isEnabled) {
      return false;
    }

    final coin = markets.cast<dynamic>().firstWhere(
      (item) => item.id == alert.coinId,
      orElse: () => null,
    );

    if (coin == null) {
      return false;
    }

    return PriceAlertEngine.shouldTrigger(
      alert: alert,
      currentPrice: coin.currentPrice,
    );
  }).toList();
});
