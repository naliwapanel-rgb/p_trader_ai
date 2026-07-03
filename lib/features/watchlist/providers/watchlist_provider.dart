import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/providers/local_storage_provider.dart';
import '../data/watchlist_repository.dart';

final watchlistRepositoryProvider = Provider<WatchlistRepository>((ref) {
  final localStorageService = ref.watch(localStorageServiceProvider);
  return WatchlistRepository(localStorageService);
});

final watchlistCoinIdsProvider =
    NotifierProvider<WatchlistNotifier, List<String>>(WatchlistNotifier.new);

class WatchlistNotifier extends Notifier<List<String>> {
  late final WatchlistRepository _repository;

  @override
  List<String> build() {
    _repository = ref.watch(watchlistRepositoryProvider);
    return _repository.getWatchlistCoinIds();
  }

  Future<void> addCoin(String coinId) async {
    await _repository.addCoin(coinId);
    state = _repository.getWatchlistCoinIds();
  }

  Future<void> removeCoin(String coinId) async {
    await _repository.removeCoin(coinId);
    state = _repository.getWatchlistCoinIds();
  }

  Future<void> toggleCoin(String coinId) async {
    if (state.contains(coinId)) {
      await removeCoin(coinId);
    } else {
      await addCoin(coinId);
    }
  }

  bool contains(String coinId) {
    return state.contains(coinId);
  }
}
