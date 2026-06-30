import '../../core/errors/app_exception.dart';
import '../../core/result/result.dart';
import '../../domain/entities/crypto_asset.dart';
import '../../domain/repositories/market_repository.dart';
import '../datasources/market_remote_datasource.dart';
import '../services/market_cache_service.dart';

class MarketRepositoryImpl implements MarketRepository {
  final MarketRemoteDataSource remoteDataSource;
  final MarketCacheService cacheService;

  const MarketRepositoryImpl({
    required this.remoteDataSource,
    required this.cacheService,
  });

  @override
  Future<Result<List<CryptoAsset>>> getTopMarkets() async {
    try {
      if (cacheService.hasValidCache) {
        return Success(cacheService.cachedMarkets!);
      }

      final markets = await remoteDataSource.fetchTopMarkets();
      cacheService.saveMarkets(markets);

      return Success(markets);
    } on AppException catch (e) {
      final cached = cacheService.cachedMarkets;

      if (cached != null && cached.isNotEmpty) {
        return Success(cached);
      }

      return Failure(e.message);
    } catch (_) {
      final cached = cacheService.cachedMarkets;

      if (cached != null && cached.isNotEmpty) {
        return Success(cached);
      }

      return const Failure('Failed to load market data');
    }
  }
}
