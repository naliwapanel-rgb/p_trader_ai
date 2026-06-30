import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../services/watchlist_service.dart';

final watchlistServiceProvider = Provider<WatchlistService>((ref) {
  return WatchlistService();
});

class WatchlistNotifier extends AsyncNotifier<List<String>> {
  @override
  Future<List<String>> build() async {
    return ref.read(watchlistServiceProvider).getWatchlist();
  }

  Future<void> toggle(String coinId) async {
    final service = ref.read(watchlistServiceProvider);
    final currentList = state.value ?? [];

    if (currentList.contains(coinId)) {
      await service.remove(coinId);
    } else {
      await service.add(coinId);
    }

    state = AsyncData(await service.getWatchlist());
  }

  bool isFavorite(String coinId) {
    return state.value?.contains(coinId) ?? false;
  }
}

final watchlistProvider =
    AsyncNotifierProvider<WatchlistNotifier, List<String>>(
      WatchlistNotifier.new,
    );
