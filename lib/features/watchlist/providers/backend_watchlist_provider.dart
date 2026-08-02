import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/backend_watchlist_item.dart';
import '../data/watchlist_remote_data_source.dart';
import '../data/watchlist_repository_impl.dart';
import '../domain/watchlist_repository.dart';
import 'backend_watchlist_state.dart';

final backendWatchlistRemoteDataSourceProvider =
    Provider<WatchlistRemoteDataSource>((ref) {
      return DioWatchlistRemoteDataSource(ref.watch(backendDioClientProvider));
    });

final backendWatchlistRepositoryProvider = Provider<WatchlistRepository>((ref) {
  return WatchlistRepositoryImpl(
    remoteDataSource: ref.watch(backendWatchlistRemoteDataSourceProvider),
  );
});

final backendWatchlistProvider =
    NotifierProvider<BackendWatchlistNotifier, BackendWatchlistState>(
      BackendWatchlistNotifier.new,
    );

class BackendWatchlistNotifier extends Notifier<BackendWatchlistState> {
  @override
  BackendWatchlistState build() {
    return const BackendWatchlistState.initial();
  }

  Future<void> loadItems({bool force = false}) async {
    if (state.isLoading) {
      return;
    }

    if (state.hasLoaded && !force) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final items = await ref
          .read(backendWatchlistRepositoryProvider)
          .listItems();

      state = state.copyWith(
        items: items,
        isLoading: false,
        hasLoaded: true,
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(isLoading: false, errorMessage: error.message);
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'The watchlist could not be loaded.',
      );
    }
  }

  Future<BackendWatchlistItem?> createItem({
    required String assetSymbol,
    String exchange = WatchlistSymbolMapper.defaultExchange,
  }) async {
    if (state.isMutating) {
      return null;
    }

    final normalizedSymbol = WatchlistSymbolMapper.toUsdtPair(assetSymbol);

    final normalizedExchange = WatchlistSymbolMapper.normalizeExchange(
      exchange,
    );

    final existing = state.findItem(
      symbol: normalizedSymbol,
      exchange: normalizedExchange,
    );

    if (existing != null) {
      return existing;
    }

    state = state.copyWith(isMutating: true, clearError: true);

    try {
      final item = await ref
          .read(backendWatchlistRepositoryProvider)
          .createItem(symbol: normalizedSymbol, exchange: normalizedExchange);

      state = state.copyWith(
        items: <BackendWatchlistItem>[...state.items, item],
        isMutating: false,
        hasLoaded: true,
        clearError: true,
      );

      return item;
    } on AppException catch (error) {
      if (error.statusCode == 409) {
        return _recoverDuplicate(
          symbol: normalizedSymbol,
          exchange: normalizedExchange,
        );
      }

      state = state.copyWith(isMutating: false, errorMessage: error.message);

      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The watchlist item could not be created.',
      );

      return null;
    }
  }

  Future<bool> deleteItem(int itemId) async {
    if (state.isMutating || itemId <= 0) {
      return false;
    }

    state = state.copyWith(isMutating: true, clearError: true);

    try {
      await ref.read(backendWatchlistRepositoryProvider).deleteItem(itemId);

      state = state.copyWith(
        items: state.items
            .where((item) => item.id != itemId)
            .toList(growable: false),
        isMutating: false,
        hasLoaded: true,
        clearError: true,
      );

      return true;
    } on AppException catch (error) {
      if (error.statusCode == 404) {
        state = state.copyWith(
          items: state.items
              .where((item) => item.id != itemId)
              .toList(growable: false),
          isMutating: false,
          hasLoaded: true,
          clearError: true,
        );

        return true;
      }

      state = state.copyWith(isMutating: false, errorMessage: error.message);

      return false;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The watchlist item could not be deleted.',
      );

      return false;
    }
  }

  Future<bool> toggleAssetSymbol({
    required String assetSymbol,
    String exchange = WatchlistSymbolMapper.defaultExchange,
  }) async {
    final existing = state.findItem(symbol: assetSymbol, exchange: exchange);

    if (existing != null) {
      return deleteItem(existing.id);
    }

    return await createItem(assetSymbol: assetSymbol, exchange: exchange) !=
        null;
  }

  void clearError() {
    state = state.copyWith(clearError: true);
  }

  Future<BackendWatchlistItem?> _recoverDuplicate({
    required String symbol,
    required String exchange,
  }) async {
    try {
      final items = await ref
          .read(backendWatchlistRepositoryProvider)
          .listItems();

      state = state.copyWith(
        items: items,
        isMutating: false,
        hasLoaded: true,
        clearError: true,
      );

      return state.findItem(symbol: symbol, exchange: exchange);
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);

      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The watchlist could not be refreshed.',
      );

      return null;
    }
  }
}
