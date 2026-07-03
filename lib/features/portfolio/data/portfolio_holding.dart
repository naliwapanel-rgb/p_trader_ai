class PortfolioHolding {
  const PortfolioHolding({
    required this.coinId,
    required this.symbol,
    required this.name,
    required this.amount,
    required this.averageBuyPrice,
  });

  final String coinId;
  final String symbol;
  final String name;
  final double amount;
  final double averageBuyPrice;

  Map<String, dynamic> toJson() {
    return {
      'coinId': coinId,
      'symbol': symbol,
      'name': name,
      'amount': amount,
      'averageBuyPrice': averageBuyPrice,
    };
  }

  factory PortfolioHolding.fromJson(Map<String, dynamic> json) {
    return PortfolioHolding(
      coinId: json['coinId'] as String,
      symbol: json['symbol'] as String,
      name: json['name'] as String,
      amount: (json['amount'] as num).toDouble(),
      averageBuyPrice: (json['averageBuyPrice'] as num).toDouble(),
    );
  }
}
