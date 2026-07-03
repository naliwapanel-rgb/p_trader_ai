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
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'symbol': symbol,
      'name': name,
      'image': image,
      'marketCapRank': marketCapRank,
      'currentPrice': currentPrice,
      'marketCap': marketCap,
      'totalVolume': totalVolume,
      'priceChangePercentage24h': priceChangePercentage24h,
      'ath': ath,
      'athChangePercentage': athChangePercentage,
      'athDate': athDate.toIso8601String(),
      'atl': atl,
      'atlChangePercentage': atlChangePercentage,
      'atlDate': atlDate.toIso8601String(),
      'lastUpdated': lastUpdated.toIso8601String(),
    };
  }

  factory CryptoAsset.fromJson(Map<String, dynamic> json) {
    return CryptoAsset(
      id: json['id'] as String,
      symbol: json['symbol'] as String,
      name: json['name'] as String,
      image: json['image'] as String,
      marketCapRank: json['marketCapRank'] as int,
      currentPrice: (json['currentPrice'] as num).toDouble(),
      marketCap: (json['marketCap'] as num).toDouble(),
      totalVolume: (json['totalVolume'] as num).toDouble(),
      priceChangePercentage24h: (json['priceChangePercentage24h'] as num)
          .toDouble(),
      ath: (json['ath'] as num).toDouble(),
      athChangePercentage: (json['athChangePercentage'] as num).toDouble(),
      athDate: DateTime.parse(json['athDate'] as String),
      atl: (json['atl'] as num).toDouble(),
      atlChangePercentage: (json['atlChangePercentage'] as num).toDouble(),
      atlDate: DateTime.parse(json['atlDate'] as String),
      lastUpdated: DateTime.parse(json['lastUpdated'] as String),
    );
  }
}
