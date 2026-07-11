import '../data/portfolio_holding.dart';

class PortfolioCalculator {
  static double currentValue({
    required PortfolioHolding holding,
    required double currentPrice,
  }) {
    return holding.amount * currentPrice;
  }

  static double costBasis(PortfolioHolding holding) {
    return holding.amount * holding.averageBuyPrice;
  }

  static double profitLoss({
    required PortfolioHolding holding,
    required double currentPrice,
  }) {
    return currentValue(holding: holding, currentPrice: currentPrice) -
        costBasis(holding);
  }

  static double profitLossPercentage({
    required PortfolioHolding holding,
    required double currentPrice,
  }) {
    final cost = costBasis(holding);

    if (cost == 0) {
      return 0;
    }

    return (profitLoss(holding: holding, currentPrice: currentPrice) / cost) *
        100;
  }
}
