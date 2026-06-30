import '../../core/result/result.dart';
import '../entities/crypto_asset.dart';
import '../repositories/market_repository.dart';

class GetTopMarkets {
  final MarketRepository repository;

  const GetTopMarkets(this.repository);

  Future<Result<List<CryptoAsset>>> call() {
    return repository.getTopMarkets();
  }
}
