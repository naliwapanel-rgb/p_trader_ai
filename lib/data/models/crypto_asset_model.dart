import '../../domain/entities/crypto_asset.dart';

class CryptoAssetModel extends CryptoAsset {
  const CryptoAssetModel({
    required super.id,
    required super.symbol,
    required super.name,
    required super.image,
    required super.marketCapRank,
    required super.currentPrice,
    required super.marketCap,
    required super.totalVolume,
    required super.priceChangePercentage24h,
    required super.ath,
    required super.athChangePercentage,
    required super.athDate,
    required super.atl,
    required super.atlChangePercentage,
    required super.atlDate,
    required super.lastUpdated,
  });

  factory CryptoAssetModel.fromJson(Map<String, dynamic> json) {
    return CryptoAssetModel(
      id: json['id'] ?? '',
      symbol: json['symbol'] ?? '',
      name: json['name'] ?? '',
      image: json['image'] ?? '',
      marketCapRank: json['market_cap_rank'] ?? 0,
      currentPrice: (json['current_price'] ?? 0).toDouble(),
      marketCap: (json['market_cap'] ?? 0).toDouble(),
      totalVolume: (json['total_volume'] ?? 0).toDouble(),
      priceChangePercentage24h: (json['price_change_percentage_24h'] ?? 0)
          .toDouble(),

      ath: (json['ath'] ?? 0).toDouble(),
      athChangePercentage: (json['ath_change_percentage'] ?? 0).toDouble(),
      athDate: DateTime.tryParse(json['ath_date'] ?? '') ?? DateTime.now(),

      atl: (json['atl'] ?? 0).toDouble(),
      atlChangePercentage: (json['atl_change_percentage'] ?? 0).toDouble(),
      atlDate: DateTime.tryParse(json['atl_date'] ?? '') ?? DateTime.now(),

      lastUpdated:
          DateTime.tryParse(json['last_updated'] ?? '') ?? DateTime.now(),
    );
  }
}
