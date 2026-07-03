import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/network/dio_client.dart';
import '../core/result/result.dart';
import '../data/datasources/market_remote_datasource.dart';
import '../data/repositories/market_repository_impl.dart';
import '../data/services/market_cache_service.dart';
import '../domain/entities/crypto_asset.dart';
import '../domain/repositories/market_repository.dart';
import '../domain/usecases/get_top_markets.dart';
import 'dart:async';
import '../core/providers/local_storage_provider.dart';

final dioClientProvider = Provider<DioClient>((ref) {
  return DioClient();
});

final marketCacheServiceProvider = Provider<MarketCacheService>((ref) {
  final prefs = ref.watch(sharedPreferencesProvider);
  return MarketCacheService(prefs);
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

final liveMarketsProvider = FutureProvider.autoDispose<List<CryptoAsset>>((
  ref,
) async {
  final timer = Timer.periodic(const Duration(seconds: 60), (_) {
    ref.invalidateSelf();
  });

  ref.onDispose(timer.cancel);

  final usecase = ref.watch(getTopMarketsProvider);
  final result = await usecase();

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
  String build() => '';

  void setQuery(String query) {
    state = query;
  }
}

final marketSearchProvider = NotifierProvider<MarketSearchNotifier, String>(
  MarketSearchNotifier.new,
);
