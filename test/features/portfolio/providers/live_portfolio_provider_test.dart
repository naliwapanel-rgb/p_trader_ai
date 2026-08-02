import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/portfolio/data/backend_portfolio.dart';
import 'package:p_trader_ai/features/portfolio/data/portfolio_sync_result.dart';
import 'package:p_trader_ai/features/portfolio/data/portfolio_sync_snapshot.dart';
import 'package:p_trader_ai/features/portfolio/domain/live_portfolio_repository.dart';
import 'package:p_trader_ai/features/portfolio/providers/live_portfolio_provider.dart';

void main() {
  group('LivePortfolioNotifier', () {
    test('loads portfolios and selects the first one', () async {
      final repository = _FakeLivePortfolioRepository(
        portfolios: <BackendPortfolio>[_portfolio()],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(livePortfolioProvider.notifier).loadPortfolios();

      final state = container.read(livePortfolioProvider);

      expect(state.portfolios, hasLength(1));
      expect(state.selectedPortfolioId, 4);
      expect(state.errorMessage, isNull);
    });

    test('creates and selects the first live portfolio', () async {
      final repository = _FakeLivePortfolioRepository();
      final container = _container(repository);
      addTearDown(container.dispose);

      final portfolio = await container
          .read(livePortfolioProvider.notifier)
          .createPortfolio();

      final state = container.read(livePortfolioProvider);

      expect(portfolio?.id, 4);
      expect(state.selectedPortfolioId, 4);
      expect(state.portfolios, hasLength(1));
      expect(state.infoMessage, 'Live portfolio created successfully.');
    });

    test('synchronization updates portfolio and snapshot', () async {
      final repository = _FakeLivePortfolioRepository(
        portfolios: <BackendPortfolio>[
          _portfolio(totalValue: 0, profitLoss: 0),
        ],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(livePortfolioProvider.notifier);

      await notifier.loadPortfolios();

      final result = await notifier.synchronize(exchangeAccountId: 1);

      final state = container.read(livePortfolioProvider);

      expect(result?.snapshot.id, 10);
      expect(state.latestSnapshot?.status, 'SUCCESS');
      expect(state.history, hasLength(1));
      expect(state.selectedPortfolio?.totalValue, 1250);
      expect(state.selectedPortfolio?.profitLoss, 25.5);
    });

    test('missing latest snapshot is not treated as error', () async {
      final repository = _FakeLivePortfolioRepository(
        portfolios: <BackendPortfolio>[_portfolio()],
        latestError: const AppException(
          'Portfolio synchronization snapshot not found',
          statusCode: 404,
        ),
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(livePortfolioProvider.notifier);

      await notifier.loadPortfolios();
      await notifier.loadLatestSnapshot();

      final state = container.read(livePortfolioProvider);

      expect(state.latestSnapshot, isNull);
      expect(state.errorMessage, isNull);
      expect(state.isLoading, isFalse);
    });
  });
}

ProviderContainer _container(LivePortfolioRepository repository) {
  return ProviderContainer(
    overrides: [livePortfolioRepositoryProvider.overrideWithValue(repository)],
  );
}

BackendPortfolio _portfolio({
  double totalValue = 1250,
  double profitLoss = 25.5,
}) {
  return BackendPortfolio(
    id: 4,
    userId: 1,
    name: 'Live Portfolio',
    baseCurrency: 'USDT',
    totalValue: totalValue,
    profitLoss: profitLoss,
    createdAt: DateTime.utc(2026, 8, 2, 12),
  );
}

PortfolioSyncSnapshot _snapshot() {
  return PortfolioSyncSnapshot(
    id: 10,
    userId: 1,
    portfolioId: 4,
    exchangeAccountId: 1,
    exchangeName: 'BYBIT',
    accountType: 'UNIFIED',
    category: 'linear',
    settleCoin: 'USDT',
    status: 'SUCCESS',
    fingerprint:
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    syncVersion: 1,
    totalEquityUsd: 1250,
    totalWalletBalanceUsd: 1200,
    totalAvailableBalanceUsd: 900,
    totalUnrealizedPnlUsd: 25.5,
    totalRealizedPnlUsd: 10,
    totalPositionValueUsd: 500,
    coinCount: 1,
    openPositionCount: 1,
    openOrderCount: 2,
    balancePayload: const <String, dynamic>{'coins': <Map<String, dynamic>>[]},
    positionsPayload: const <Map<String, dynamic>>[],
    ordersPayload: const <Map<String, dynamic>>[],
    syncedAt: DateTime.utc(2026, 8, 2, 12, 5),
    createdAt: DateTime.utc(2026, 8, 2, 12, 5),
  );
}

class _FakeLivePortfolioRepository implements LivePortfolioRepository {
  _FakeLivePortfolioRepository({
    this.portfolios = const <BackendPortfolio>[],
    this.latestError,
  });

  List<BackendPortfolio> portfolios;
  final AppException? latestError;

  @override
  Future<List<BackendPortfolio>> listPortfolios() async {
    return portfolios;
  }

  @override
  Future<BackendPortfolio> createPortfolio({
    required String name,
    required String baseCurrency,
  }) async {
    final portfolio = _portfolio().copyWith(
      name: name,
      baseCurrency: baseCurrency,
      totalValue: 0,
      profitLoss: 0,
    );

    portfolios = <BackendPortfolio>[...portfolios, portfolio];

    return portfolio;
  }

  @override
  Future<PortfolioSyncResult> synchronize({
    required int portfolioId,
    required int exchangeAccountId,
    required String category,
    required String settleCoin,
  }) async {
    return PortfolioSyncResult(
      snapshot: _snapshot(),
      created: true,
      portfolioTotalValue: 1250,
      portfolioProfitLoss: 25.5,
      sourceErrors: const <String, String>{},
    );
  }

  @override
  Future<PortfolioSyncSnapshot> getLatestSnapshot({
    required int portfolioId,
    int? exchangeAccountId,
  }) async {
    final error = latestError;

    if (error != null) {
      throw error;
    }

    return _snapshot();
  }

  @override
  Future<List<PortfolioSyncSnapshot>> listSyncHistory({
    required int portfolioId,
    int limit = 50,
  }) async {
    return <PortfolioSyncSnapshot>[_snapshot()];
  }
}
