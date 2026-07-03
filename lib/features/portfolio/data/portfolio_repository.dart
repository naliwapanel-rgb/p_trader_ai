import 'dart:convert';

import '../../../core/services/local_storage_service.dart';
import 'portfolio_holding.dart';

class PortfolioRepository {
  PortfolioRepository(this._localStorageService);

  final LocalStorageService _localStorageService;

  static const String _holdingsKey = 'portfolio_holdings';

  List<PortfolioHolding> getHoldings() {
    final rawHoldings = _localStorageService.getStringList(_holdingsKey);

    return rawHoldings
        .map((raw) => PortfolioHolding.fromJson(jsonDecode(raw)))
        .toList();
  }

  Future<void> saveHoldings(List<PortfolioHolding> holdings) async {
    final encodedHoldings = holdings
        .map((holding) => jsonEncode(holding.toJson()))
        .toList();

    await _localStorageService.setStringList(_holdingsKey, encodedHoldings);
  }

  Future<void> addHolding(PortfolioHolding holding) async {
    final currentHoldings = getHoldings();

    final existingIndex = currentHoldings.indexWhere(
      (item) => item.coinId == holding.coinId,
    );

    if (existingIndex == -1) {
      await saveHoldings([...currentHoldings, holding]);
      return;
    }

    final existing = currentHoldings[existingIndex];

    final totalAmount = existing.amount + holding.amount;

    final totalCost =
        (existing.amount * existing.averageBuyPrice) +
        (holding.amount * holding.averageBuyPrice);

    final updatedHolding = PortfolioHolding(
      coinId: existing.coinId,
      symbol: existing.symbol,
      name: existing.name,
      amount: totalAmount,
      averageBuyPrice: totalCost / totalAmount,
    );

    currentHoldings[existingIndex] = updatedHolding;

    await saveHoldings(currentHoldings);
  }

  Future<void> removeHolding(String coinId) async {
    final updatedHoldings = getHoldings()
        .where((holding) => holding.coinId != coinId)
        .toList();

    await saveHoldings(updatedHoldings);
  }

  Future<void> clearHoldings() async {
    await _localStorageService.remove(_holdingsKey);
  }
}
