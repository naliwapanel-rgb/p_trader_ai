import '../domain/live_portfolio_repository.dart';
import 'backend_portfolio.dart';
import 'live_portfolio_remote_data_source.dart';
import 'portfolio_sync_result.dart';
import 'portfolio_sync_snapshot.dart';

class LivePortfolioRepositoryImpl implements LivePortfolioRepository {
  const LivePortfolioRepositoryImpl({
    required LivePortfolioRemoteDataSource remoteDataSource,
  }) : _remoteDataSource = remoteDataSource;

  final LivePortfolioRemoteDataSource _remoteDataSource;

  @override
  Future<List<BackendPortfolio>> listPortfolios() {
    return _remoteDataSource.listPortfolios();
  }

  @override
  Future<BackendPortfolio> createPortfolio({
    required String name,
    required String baseCurrency,
  }) {
    return _remoteDataSource.createPortfolio(
      name: name,
      baseCurrency: baseCurrency,
    );
  }

  @override
  Future<PortfolioSyncResult> synchronize({
    required int portfolioId,
    required int exchangeAccountId,
    required String category,
    required String settleCoin,
  }) {
    return _remoteDataSource.synchronize(
      portfolioId: portfolioId,
      exchangeAccountId: exchangeAccountId,
      category: category,
      settleCoin: settleCoin,
    );
  }

  @override
  Future<PortfolioSyncSnapshot> getLatestSnapshot({
    required int portfolioId,
    int? exchangeAccountId,
  }) {
    return _remoteDataSource.getLatestSnapshot(
      portfolioId: portfolioId,
      exchangeAccountId: exchangeAccountId,
    );
  }

  @override
  Future<List<PortfolioSyncSnapshot>> listSyncHistory({
    required int portfolioId,
    int limit = 50,
  }) {
    return _remoteDataSource.listSyncHistory(
      portfolioId: portfolioId,
      limit: limit,
    );
  }
}
