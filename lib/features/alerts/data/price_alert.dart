enum PriceAlertCondition { above, below }

class PriceAlert {
  const PriceAlert({
    required this.id,
    required this.coinId,
    required this.symbol,
    required this.targetPrice,
    required this.condition,
    required this.isEnabled,
    required this.createdAt,
  });

  final String id;
  final String coinId;
  final String symbol;
  final double targetPrice;
  final PriceAlertCondition condition;
  final bool isEnabled;
  final DateTime createdAt;

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'coinId': coinId,
      'symbol': symbol,
      'targetPrice': targetPrice,
      'condition': condition.name,
      'isEnabled': isEnabled,
      'createdAt': createdAt.toIso8601String(),
    };
  }

  factory PriceAlert.fromJson(Map<String, dynamic> json) {
    return PriceAlert(
      id: json['id'] as String,
      coinId: json['coinId'] as String,
      symbol: json['symbol'] as String,
      targetPrice: (json['targetPrice'] as num).toDouble(),
      condition: PriceAlertCondition.values.byName(json['condition'] as String),
      isEnabled: json['isEnabled'] as bool,
      createdAt: DateTime.parse(json['createdAt'] as String),
    );
  }

  PriceAlert copyWith({
    String? id,
    String? coinId,
    String? symbol,
    double? targetPrice,
    PriceAlertCondition? condition,
    bool? isEnabled,
    DateTime? createdAt,
  }) {
    return PriceAlert(
      id: id ?? this.id,
      coinId: coinId ?? this.coinId,
      symbol: symbol ?? this.symbol,
      targetPrice: targetPrice ?? this.targetPrice,
      condition: condition ?? this.condition,
      isEnabled: isEnabled ?? this.isEnabled,
      createdAt: createdAt ?? this.createdAt,
    );
  }
}
