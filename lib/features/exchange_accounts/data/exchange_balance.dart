class ExchangeCoinBalance {
  const ExchangeCoinBalance({
    required this.symbol,
    required this.walletBalance,
    required this.availableBalance,
    required this.lockedBalance,
  });

  final String symbol;
  final double walletBalance;
  final double availableBalance;
  final double lockedBalance;

  factory ExchangeCoinBalance.fromJson(Map<String, dynamic> json) {
    final symbolValue = json['coin'] ?? json['symbol'];

    return ExchangeCoinBalance(
      symbol: symbolValue is String && symbolValue.trim().isNotEmpty
          ? symbolValue.trim().toUpperCase()
          : 'UNKNOWN',
      walletBalance: _asDouble(
        json['wallet_balance'] ?? json['walletBalance'] ?? json['balance'],
      ),
      availableBalance: _asDouble(
        json['available_balance'] ??
            json['availableBalance'] ??
            json['available'],
      ),
      lockedBalance: _asDouble(
        json['locked_balance'] ?? json['lockedBalance'] ?? json['locked'],
      ),
    );
  }
}

class ExchangeBalance {
  const ExchangeBalance({
    required this.accountType,
    required this.totalEquityUsd,
    required this.totalWalletBalanceUsd,
    required this.totalAvailableBalanceUsd,
    required this.totalUnrealizedPnlUsd,
    required this.coins,
  });

  final String accountType;
  final double totalEquityUsd;
  final double totalWalletBalanceUsd;
  final double totalAvailableBalanceUsd;
  final double totalUnrealizedPnlUsd;
  final List<ExchangeCoinBalance> coins;

  factory ExchangeBalance.fromJson(Map<String, dynamic> json) {
    final accountType = json['account_type'];
    final rawCoins = json['coins'];

    final coins = <ExchangeCoinBalance>[];

    if (rawCoins is List) {
      for (final item in rawCoins) {
        if (item is Map) {
          coins.add(
            ExchangeCoinBalance.fromJson(Map<String, dynamic>.from(item)),
          );
        }
      }
    }

    return ExchangeBalance(
      accountType: accountType is String && accountType.trim().isNotEmpty
          ? accountType.trim().toUpperCase()
          : 'UNKNOWN',
      totalEquityUsd: _asDouble(json['total_equity_usd']),
      totalWalletBalanceUsd: _asDouble(json['total_wallet_balance_usd']),
      totalAvailableBalanceUsd: _asDouble(json['total_available_balance_usd']),
      totalUnrealizedPnlUsd: _asDouble(json['total_unrealized_pnl_usd']),
      coins: List<ExchangeCoinBalance>.unmodifiable(coins),
    );
  }
}

double _asDouble(Object? value) {
  if (value is num) {
    return value.toDouble();
  }

  if (value is String) {
    return double.tryParse(value.trim()) ?? 0;
  }

  return 0;
}
