import '../data/backend_portfolio.dart';
import '../data/portfolio_sync_result.dart';
import '../data/portfolio_sync_snapshot.dart';

abstract interface class LivePortfolioRepository {
  Future<List<BackendPortfolio>> listPortfolios();

  Future<BackendPortfolio> createPortfolio({
    required String name,
    required String baseCurrency,
  });

  Future<PortfolioSyncResult> synchronize({
    required int portfolioId,
    required int exchangeAccountId,
    required String category,
    required String settleCoin,
  });

  Future<PortfolioSyncSnapshot> getLatestSnapshot({
    required int portfolioId,
    int? exchangeAccountId,
  });

  Future<List<PortfolioSyncSnapshot>> listSyncHistory({
    required int portfolioId,
    int limit = 50,
  });
}
