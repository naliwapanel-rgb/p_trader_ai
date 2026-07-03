import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/local_storage_provider.dart';
import '../data/portfolio_holding.dart';
import '../data/portfolio_repository.dart';

final portfolioRepositoryProvider = Provider<PortfolioRepository>((ref) {
  final localStorageService = ref.watch(localStorageServiceProvider);
  return PortfolioRepository(localStorageService);
});

final portfolioHoldingsProvider =
    NotifierProvider<PortfolioNotifier, List<PortfolioHolding>>(
      PortfolioNotifier.new,
    );

class PortfolioNotifier extends Notifier<List<PortfolioHolding>> {
  late final PortfolioRepository _repository;

  @override
  List<PortfolioHolding> build() {
    _repository = ref.watch(portfolioRepositoryProvider);
    return _repository.getHoldings();
  }

  Future<void> addHolding(PortfolioHolding holding) async {
    await _repository.addHolding(holding);
    state = _repository.getHoldings();
  }

  Future<void> removeHolding(String coinId) async {
    await _repository.removeHolding(coinId);
    state = _repository.getHoldings();
  }

  Future<void> clearHoldings() async {
    await _repository.clearHoldings();
    state = [];
  }
}
