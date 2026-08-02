class PortfolioSyncCoin {
  const PortfolioSyncCoin({
    required this.coin,
    required this.equity,
    required this.walletBalance,
    required this.availableBalance,
    required this.lockedBalance,
    required this.usdValue,
    required this.unrealizedPnl,
  });

  final String coin;
  final double equity;
  final double walletBalance;
  final double availableBalance;
  final double lockedBalance;
  final double usdValue;
  final double unrealizedPnl;

  factory PortfolioSyncCoin.fromJson(Map<String, dynamic> json) {
    final coin = json['coin'];

    if (coin is! String || coin.trim().isEmpty) {
      throw const FormatException('A synchronized coin balance is invalid.');
    }

    return PortfolioSyncCoin(
      coin: coin.trim().toUpperCase(),
      equity: _numberOrZero(json['equity']),
      walletBalance: _numberOrZero(json['wallet_balance']),
      availableBalance: _numberOrZero(json['available_balance']),
      lockedBalance: _numberOrZero(json['locked_balance']),
      usdValue: _numberOrZero(json['usd_value']),
      unrealizedPnl: _numberOrZero(json['unrealized_pnl']),
    );
  }
}

double _numberOrZero(Object? value) {
  return value is num ? value.toDouble() : 0;
}
