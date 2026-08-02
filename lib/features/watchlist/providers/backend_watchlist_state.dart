import '../data/backend_watchlist_item.dart';

class BackendWatchlistState {
  const BackendWatchlistState({
    required this.items,
    required this.isLoading,
    required this.isMutating,
    required this.hasLoaded,
    this.errorMessage,
  });

  const BackendWatchlistState.initial()
    : items = const <BackendWatchlistItem>[],
      isLoading = false,
      isMutating = false,
      hasLoaded = false,
      errorMessage = null;

  final List<BackendWatchlistItem> items;
  final bool isLoading;
  final bool isMutating;
  final bool hasLoaded;
  final String? errorMessage;

  BackendWatchlistItem? findItem({
    required String symbol,
    required String exchange,
  }) {
    final normalizedSymbol = WatchlistSymbolMapper.toUsdtPair(symbol);

    final normalizedExchange = WatchlistSymbolMapper.normalizeExchange(
      exchange,
    );

    for (final item in items) {
      if (item.symbol == normalizedSymbol &&
          item.exchange == normalizedExchange) {
        return item;
      }
    }

    return null;
  }

  BackendWatchlistState copyWith({
    List<BackendWatchlistItem>? items,
    bool? isLoading,
    bool? isMutating,
    bool? hasLoaded,
    String? errorMessage,
    bool clearError = false,
  }) {
    return BackendWatchlistState(
      items: items ?? this.items,
      isLoading: isLoading ?? this.isLoading,
      isMutating: isMutating ?? this.isMutating,
      hasLoaded: hasLoaded ?? this.hasLoaded,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
    );
  }
}
