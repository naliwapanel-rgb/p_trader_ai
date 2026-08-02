import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/portfolio/data/backend_portfolio.dart';
import 'package:p_trader_ai/features/portfolio/data/portfolio_sync_snapshot.dart';
import 'package:p_trader_ai/features/portfolio/providers/live_portfolio_state.dart';

void main() {
  group('LivePortfolioState', () {
    test('returns the selected portfolio', () {
      final portfolio = _portfolio(id: 4);

      final state = LivePortfolioState(
        isLoading: false,
        isMutating: false,
        portfolios: <BackendPortfolio>[portfolio, _portfolio(id: 5)],
        selectedPortfolioId: 4,
        history: const <PortfolioSyncSnapshot>[],
      );

      expect(state.selectedPortfolio, same(portfolio));
    });

    test('can clear snapshot and selection', () {
      final snapshot = _snapshot();

      final state = LivePortfolioState(
        isLoading: false,
        isMutating: false,
        portfolios: <BackendPortfolio>[_portfolio(id: 4)],
        selectedPortfolioId: 4,
        latestSnapshot: snapshot,
        history: <PortfolioSyncSnapshot>[snapshot],
      );

      final cleared = state.copyWith(
        selectedPortfolioId: null,
        latestSnapshot: null,
        history: const <PortfolioSyncSnapshot>[],
      );

      expect(cleared.selectedPortfolioId, isNull);
      expect(cleared.selectedPortfolio, isNull);
      expect(cleared.latestSnapshot, isNull);
      expect(cleared.history, isEmpty);
    });
  });
}

BackendPortfolio _portfolio({required int id}) {
  return BackendPortfolio(
    id: id,
    userId: 1,
    name: 'Portfolio $id',
    baseCurrency: 'USDT',
    totalValue: 0,
    profitLoss: 0,
    createdAt: DateTime.utc(2026, 8, 2),
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
    totalEquityUsd: 0,
    totalWalletBalanceUsd: 0,
    totalAvailableBalanceUsd: 0,
    totalUnrealizedPnlUsd: 0,
    totalRealizedPnlUsd: 0,
    totalPositionValueUsd: 0,
    coinCount: 0,
    openPositionCount: 0,
    openOrderCount: 0,
    balancePayload: const <String, dynamic>{},
    positionsPayload: const <Map<String, dynamic>>[],
    ordersPayload: const <Map<String, dynamic>>[],
    syncedAt: DateTime.utc(2026, 8, 2),
    createdAt: DateTime.utc(2026, 8, 2),
  );
}
