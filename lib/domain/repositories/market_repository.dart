import '../../core/result/result.dart';
import '../entities/crypto_asset.dart';

abstract class MarketRepository {
  Future<Result<List<CryptoAsset>>> getTopMarkets();
}
