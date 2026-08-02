import '../data/backend_portfolio.dart';
import '../data/portfolio_sync_snapshot.dart';

const Object _notProvided = Object();

class LivePortfolioState {
  const LivePortfolioState({
    required this.isLoading,
    required this.isMutating,
    required this.portfolios,
    required this.history,
    this.selectedPortfolioId,
    this.latestSnapshot,
    this.errorMessage,
    this.infoMessage,
  });

  const LivePortfolioState.initial()
    : isLoading = false,
      isMutating = false,
      portfolios = const <BackendPortfolio>[],
      history = const <PortfolioSyncSnapshot>[],
      selectedPortfolioId = null,
      latestSnapshot = null,
      errorMessage = null,
      infoMessage = null;

  final bool isLoading;
  final bool isMutating;

  final List<BackendPortfolio> portfolios;
  final int? selectedPortfolioId;

  final PortfolioSyncSnapshot? latestSnapshot;
  final List<PortfolioSyncSnapshot> history;

  final String? errorMessage;
  final String? infoMessage;

  BackendPortfolio? get selectedPortfolio {
    final portfolioId = selectedPortfolioId;

    if (portfolioId == null) {
      return null;
    }

    for (final portfolio in portfolios) {
      if (portfolio.id == portfolioId) {
        return portfolio;
      }
    }

    return null;
  }

  LivePortfolioState copyWith({
    bool? isLoading,
    bool? isMutating,
    List<BackendPortfolio>? portfolios,
    Object? selectedPortfolioId = _notProvided,
    Object? latestSnapshot = _notProvided,
    List<PortfolioSyncSnapshot>? history,
    String? errorMessage,
    String? infoMessage,
    bool clearError = false,
    bool clearInfo = false,
  }) {
    return LivePortfolioState(
      isLoading: isLoading ?? this.isLoading,
      isMutating: isMutating ?? this.isMutating,
      portfolios: portfolios ?? this.portfolios,
      selectedPortfolioId: identical(selectedPortfolioId, _notProvided)
          ? this.selectedPortfolioId
          : selectedPortfolioId as int?,
      latestSnapshot: identical(latestSnapshot, _notProvided)
          ? this.latestSnapshot
          : latestSnapshot as PortfolioSyncSnapshot?,
      history: history ?? this.history,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      infoMessage: clearInfo ? null : infoMessage ?? this.infoMessage,
    );
  }
}
