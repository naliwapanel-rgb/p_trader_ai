import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/backend_portfolio.dart';
import '../data/live_portfolio_remote_data_source.dart';
import '../data/live_portfolio_repository_impl.dart';
import '../data/portfolio_sync_result.dart';
import '../data/portfolio_sync_snapshot.dart';
import '../domain/live_portfolio_repository.dart';
import 'live_portfolio_state.dart';

final livePortfolioRemoteDataSourceProvider =
    Provider<LivePortfolioRemoteDataSource>((ref) {
      return DioLivePortfolioRemoteDataSource(
        ref.watch(backendDioClientProvider),
      );
    });

final livePortfolioRepositoryProvider = Provider<LivePortfolioRepository>((
  ref,
) {
  return LivePortfolioRepositoryImpl(
    remoteDataSource: ref.watch(livePortfolioRemoteDataSourceProvider),
  );
});

final livePortfolioProvider =
    NotifierProvider<LivePortfolioNotifier, LivePortfolioState>(
      LivePortfolioNotifier.new,
    );

class LivePortfolioNotifier extends Notifier<LivePortfolioState> {
  @override
  LivePortfolioState build() {
    return const LivePortfolioState.initial();
  }

  Future<void> loadPortfolios() async {
    if (state.isLoading) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearInfo: true);

    try {
      final portfolios = await ref
          .read(livePortfolioRepositoryProvider)
          .listPortfolios();

      final currentId = state.selectedPortfolioId;

      final selectedId =
          portfolios.any((portfolio) => portfolio.id == currentId)
          ? currentId
          : portfolios.isEmpty
          ? null
          : portfolios.first.id;

      state = state.copyWith(
        isLoading: false,
        portfolios: portfolios,
        selectedPortfolioId: selectedId,
        latestSnapshot: selectedId == state.selectedPortfolioId
            ? state.latestSnapshot
            : null,
        history: selectedId == state.selectedPortfolioId
            ? state.history
            : const [],
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(isLoading: false, errorMessage: error.message);
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Backend portfolios could not be loaded.',
      );
    }
  }

  Future<BackendPortfolio?> createPortfolio({
    String name = 'Live Portfolio',
    String baseCurrency = 'USDT',
  }) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      final portfolio = await ref
          .read(livePortfolioRepositoryProvider)
          .createPortfolio(name: name, baseCurrency: baseCurrency);

      state = state.copyWith(
        isMutating: false,
        portfolios: <BackendPortfolio>[...state.portfolios, portfolio],
        selectedPortfolioId: portfolio.id,
        latestSnapshot: null,
        history: const [],
        infoMessage: 'Live portfolio created successfully.',
        clearError: true,
      );

      return portfolio;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The live portfolio could not be created.',
      );
      return null;
    }
  }

  void selectPortfolio(int portfolioId) {
    if (!state.portfolios.any((portfolio) => portfolio.id == portfolioId)) {
      return;
    }

    if (portfolioId == state.selectedPortfolioId) {
      return;
    }

    state = state.copyWith(
      selectedPortfolioId: portfolioId,
      latestSnapshot: null,
      history: const [],
      clearError: true,
      clearInfo: true,
    );
  }

  Future<PortfolioSyncResult?> synchronize({
    required int exchangeAccountId,
    String category = 'linear',
    String settleCoin = 'USDT',
  }) async {
    if (state.isMutating) {
      return null;
    }

    final portfolioId = state.selectedPortfolioId;

    if (portfolioId == null) {
      state = state.copyWith(
        errorMessage: 'Create or select a live portfolio before synchronizing.',
        clearInfo: true,
      );
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      final result = await ref
          .read(livePortfolioRepositoryProvider)
          .synchronize(
            portfolioId: portfolioId,
            exchangeAccountId: exchangeAccountId,
            category: category,
            settleCoin: settleCoin,
          );

      final portfolios = state.portfolios
          .map(
            (portfolio) => portfolio.id == portfolioId
                ? portfolio.copyWith(
                    totalValue: result.portfolioTotalValue,
                    profitLoss: result.portfolioProfitLoss,
                  )
                : portfolio,
          )
          .toList(growable: false);

      final history = <PortfolioSyncSnapshot>[
        result.snapshot,
        ...state.history.where((snapshot) => snapshot.id != result.snapshot.id),
      ];

      final statusMessage = switch (result.snapshot.status) {
        'SUCCESS' => 'Portfolio synchronization completed successfully.',
        'PARTIAL' => 'Portfolio synchronization completed with partial data.',
        _ => 'Portfolio synchronization failed.',
      };

      state = state.copyWith(
        isMutating: false,
        portfolios: portfolios,
        latestSnapshot: result.snapshot,
        history: history,
        infoMessage: statusMessage,
        clearError: true,
      );

      return result;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The portfolio synchronization failed.',
      );
      return null;
    }
  }

  Future<void> loadLatestSnapshot({int? exchangeAccountId}) async {
    final portfolioId = state.selectedPortfolioId;

    if (portfolioId == null || state.isLoading) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearInfo: true);

    try {
      final snapshot = await ref
          .read(livePortfolioRepositoryProvider)
          .getLatestSnapshot(
            portfolioId: portfolioId,
            exchangeAccountId: exchangeAccountId,
          );

      state = state.copyWith(
        isLoading: false,
        latestSnapshot: snapshot,
        clearError: true,
      );
    } on AppException catch (error) {
      if (error.statusCode == 404) {
        state = state.copyWith(
          isLoading: false,
          latestSnapshot: null,
          clearError: true,
        );
        return;
      }

      state = state.copyWith(isLoading: false, errorMessage: error.message);
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'The latest synchronization could not be loaded.',
      );
    }
  }

  Future<void> loadSyncHistory({int limit = 50}) async {
    final portfolioId = state.selectedPortfolioId;

    if (portfolioId == null || state.isLoading) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearInfo: true);

    try {
      final history = await ref
          .read(livePortfolioRepositoryProvider)
          .listSyncHistory(portfolioId: portfolioId, limit: limit);

      state = state.copyWith(
        isLoading: false,
        history: history,
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(isLoading: false, errorMessage: error.message);
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Portfolio synchronization history could not be loaded.',
      );
    }
  }

  void clearMessages() {
    state = state.copyWith(clearError: true, clearInfo: true);
  }
}
