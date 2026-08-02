import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/network/dio_client.dart';
import '../core/providers/local_storage_provider.dart';
import '../core/result/result.dart';
import '../data/datasources/market_remote_datasource.dart';
import '../data/repositories/market_repository_impl.dart';
import '../data/services/market_cache_service.dart';
import '../domain/entities/crypto_asset.dart';
import '../domain/repositories/market_repository.dart';
import '../domain/usecases/get_top_markets.dart';

final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient();
});

final marketCacheServiceProvider = Provider<MarketCacheService>((ref) {
  final preferences = ref.watch(sharedPreferencesProvider);

  return MarketCacheService(preferences);
});

final marketRemoteDataSourceProvider = Provider<MarketRemoteDataSource>((ref) {
  return MarketRemoteDataSource(ref.watch(dioClientProvider));
});

final marketRepositoryProvider = Provider<MarketRepository>((ref) {
  return MarketRepositoryImpl(
    remoteDataSource: ref.watch(marketRemoteDataSourceProvider),
    cacheService: ref.watch(marketCacheServiceProvider),
  );
});

final getTopMarketsProvider = Provider<GetTopMarkets>((ref) {
  return GetTopMarkets(ref.watch(marketRepositoryProvider));
});

/// Shared for the complete application session.
///
/// Markets, Watchlist, Alerts and Portfolio now consume the same
/// resolved future instead of each screen recreating an auto-disposed
/// provider. A deliberate refresh from Markets still clears the cache
/// and invalidates this provider.
final liveMarketsProvider = FutureProvider<List<CryptoAsset>>((ref) async {
  final useCase = ref.watch(getTopMarketsProvider);
  final result = await useCase();

  return switch (result) {
    Success<List<CryptoAsset>>(:final data) => data,
    Failure<List<CryptoAsset>>(:final message) => throw Exception(message),
  };
});

enum MarketFilter { all, gainers, losers }

class MarketFilterNotifier extends Notifier<MarketFilter> {
  @override
  MarketFilter build() {
    return MarketFilter.all;
  }

  void setFilter(MarketFilter filter) {
    state = filter;
  }
}

final marketFilterProvider =
    NotifierProvider<MarketFilterNotifier, MarketFilter>(
      MarketFilterNotifier.new,
    );

class MarketSearchNotifier extends Notifier<String> {
  @override
  String build() {
    return '';
  }

  void setQuery(String query) {
    state = query;
  }
}

final marketSearchProvider = NotifierProvider<MarketSearchNotifier, String>(
  MarketSearchNotifier.new,
);
