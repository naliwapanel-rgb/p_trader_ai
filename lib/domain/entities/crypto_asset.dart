class CryptoAsset {
  final String id;
  final String symbol;
  final String name;
  final String image;

  final int marketCapRank;

  final double currentPrice;
  final double marketCap;
  final double totalVolume;
  final double priceChangePercentage24h;

  // NEW
  final double ath;
  final double athChangePercentage;
  final DateTime athDate;

  final double atl;
  final double atlChangePercentage;
  final DateTime atlDate;

  final DateTime lastUpdated;

  const CryptoAsset({
    required this.id,
    required this.symbol,
    required this.name,
    required this.image,
    required this.marketCapRank,
    required this.currentPrice,
    required this.marketCap,
    required this.totalVolume,
    required this.priceChangePercentage24h,

    required this.ath,
    required this.athChangePercentage,
    required this.athDate,

    required this.atl,
    required this.atlChangePercentage,
    required this.atlDate,

    required this.lastUpdated,
  });
}
