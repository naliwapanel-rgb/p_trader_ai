import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../providers/market_providers.dart';
import '../data/backend_price_alert.dart';
import 'backend_price_alert_provider.dart';

final triggeredAlertsProvider = Provider<List<BackendPriceAlert>>((ref) {
  final alertState = ref.watch(backendPriceAlertProvider);
  final marketsAsync = ref.watch(liveMarketsProvider);
  final markets = marketsAsync.value ?? const [];

  return alertState.enabledAlerts
      .where((alert) {
        if (alert.triggered) {
          return true;
        }

        dynamic matchingMarket;

        for (final market in markets) {
          try {
            final dynamic candidate = market;
            final symbol = candidate.symbol?.toString().toUpperCase();

            if (symbol == alert.baseAssetSymbol) {
              matchingMarket = candidate;
              break;
            }
          } catch (_) {
            continue;
          }
        }

        if (matchingMarket == null) {
          return false;
        }

        final double currentPrice;

        try {
          final dynamic rawPrice = matchingMarket.currentPrice;

          if (rawPrice is! num) {
            return false;
          }

          currentPrice = rawPrice.toDouble();
        } catch (_) {
          return false;
        }

        if (!currentPrice.isFinite || currentPrice <= 0) {
          return false;
        }

        switch (alert.condition) {
          case BackendPriceAlertCondition.above:
            return currentPrice >= alert.targetPrice;
          case BackendPriceAlertCondition.below:
            return currentPrice <= alert.targetPrice;
        }
      })
      .toList(growable: false);
});
