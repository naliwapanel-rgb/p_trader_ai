import '../data/price_alert.dart';

class PriceAlertEngine {
  static bool shouldTrigger({
    required PriceAlert alert,
    required double currentPrice,
  }) {
    switch (alert.condition) {
      case PriceAlertCondition.above:
        return currentPrice >= alert.targetPrice;

      case PriceAlertCondition.below:
        return currentPrice <= alert.targetPrice;
    }
  }
}
