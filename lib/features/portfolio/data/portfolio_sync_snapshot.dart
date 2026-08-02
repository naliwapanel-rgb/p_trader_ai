import 'portfolio_sync_coin.dart';

class PortfolioSyncSnapshot {
  const PortfolioSyncSnapshot({
    required this.id,
    required this.userId,
    required this.portfolioId,
    required this.exchangeAccountId,
    required this.exchangeName,
    required this.accountType,
    required this.category,
    required this.settleCoin,
    required this.status,
    required this.fingerprint,
    required this.syncVersion,
    required this.totalEquityUsd,
    required this.totalWalletBalanceUsd,
    required this.totalAvailableBalanceUsd,
    required this.totalUnrealizedPnlUsd,
    required this.totalRealizedPnlUsd,
    required this.totalPositionValueUsd,
    required this.coinCount,
    required this.openPositionCount,
    required this.openOrderCount,
    required this.balancePayload,
    required this.positionsPayload,
    required this.ordersPayload,
    required this.syncedAt,
    required this.createdAt,
    this.errorMessage,
  });

  final int id;
  final int userId;
  final int portfolioId;
  final int exchangeAccountId;

  final String exchangeName;
  final String accountType;
  final String category;
  final String settleCoin;
  final String status;
  final String fingerprint;

  final int syncVersion;

  final double totalEquityUsd;
  final double totalWalletBalanceUsd;
  final double totalAvailableBalanceUsd;
  final double totalUnrealizedPnlUsd;
  final double totalRealizedPnlUsd;
  final double totalPositionValueUsd;

  final int coinCount;
  final int openPositionCount;
  final int openOrderCount;

  final Map<String, dynamic> balancePayload;
  final List<Map<String, dynamic>> positionsPayload;
  final List<Map<String, dynamic>> ordersPayload;

  final String? errorMessage;
  final DateTime syncedAt;
  final DateTime createdAt;

  bool get isSuccessful => status == 'SUCCESS';

  bool get isPartial => status == 'PARTIAL';

  bool get isFailed => status == 'FAILED';

  List<PortfolioSyncCoin> get coins {
    final rawCoins = balancePayload['coins'];

    if (rawCoins is! List) {
      return const <PortfolioSyncCoin>[];
    }

    final parsedCoins = <PortfolioSyncCoin>[];

    for (final entry in rawCoins) {
      if (entry is! Map) {
        continue;
      }

      try {
        parsedCoins.add(
          PortfolioSyncCoin.fromJson(Map<String, dynamic>.from(entry)),
        );
      } on FormatException {
        continue;
      }
    }

    return List<PortfolioSyncCoin>.unmodifiable(parsedCoins);
  }

  factory PortfolioSyncSnapshot.fromJson(Map<String, dynamic> json) {
    final exchangeName = _requiredString(
      json['exchange_name'],
      'The synchronized exchange name is invalid.',
    );

    final accountType = _requiredString(
      json['account_type'],
      'The synchronized account type is invalid.',
    );

    final category = _requiredString(
      json['category'],
      'The synchronized category is invalid.',
    );

    final settleCoin = _requiredString(
      json['settle_coin'],
      'The synchronized settlement coin is invalid.',
    );

    final status = _requiredString(
      json['status'],
      'The synchronization status is invalid.',
    ).toUpperCase();

    if (!const <String>{'SUCCESS', 'PARTIAL', 'FAILED'}.contains(status)) {
      throw const FormatException('The synchronization status is invalid.');
    }

    final fingerprint = _requiredString(
      json['fingerprint'],
      'The synchronization fingerprint is invalid.',
    );

    final errorMessageValue = json['error_message'];

    if (errorMessageValue != null && errorMessageValue is! String) {
      throw const FormatException(
        'The synchronization error message is invalid.',
      );
    }

    return PortfolioSyncSnapshot(
      id: _requiredInt(
        json['id'],
        'The synchronization snapshot ID is invalid.',
      ),
      userId: _requiredInt(
        json['user_id'],
        'The synchronization user ID is invalid.',
      ),
      portfolioId: _requiredInt(
        json['portfolio_id'],
        'The synchronized portfolio ID is invalid.',
      ),
      exchangeAccountId: _requiredInt(
        json['exchange_account_id'],
        'The synchronized exchange account ID is invalid.',
      ),
      exchangeName: exchangeName.toUpperCase(),
      accountType: accountType.toUpperCase(),
      category: category.toLowerCase(),
      settleCoin: settleCoin.toUpperCase(),
      status: status,
      fingerprint: fingerprint,
      syncVersion: _requiredInt(
        json['sync_version'],
        'The synchronization version is invalid.',
      ),
      totalEquityUsd: _requiredDouble(
        json['total_equity_usd'],
        'The synchronized equity is invalid.',
      ),
      totalWalletBalanceUsd: _requiredDouble(
        json['total_wallet_balance_usd'],
        'The synchronized wallet balance is invalid.',
      ),
      totalAvailableBalanceUsd: _requiredDouble(
        json['total_available_balance_usd'],
        'The synchronized available balance is invalid.',
      ),
      totalUnrealizedPnlUsd: _requiredDouble(
        json['total_unrealized_pnl_usd'],
        'The synchronized unrealized profit or loss is invalid.',
      ),
      totalRealizedPnlUsd: _requiredDouble(
        json['total_realized_pnl_usd'],
        'The synchronized realized profit or loss is invalid.',
      ),
      totalPositionValueUsd: _requiredDouble(
        json['total_position_value_usd'],
        'The synchronized position value is invalid.',
      ),
      coinCount: _requiredInt(
        json['coin_count'],
        'The synchronized coin count is invalid.',
      ),
      openPositionCount: _requiredInt(
        json['open_position_count'],
        'The synchronized position count is invalid.',
      ),
      openOrderCount: _requiredInt(
        json['open_order_count'],
        'The synchronized order count is invalid.',
      ),
      balancePayload: _requiredMap(
        json['balance_payload'],
        'The synchronized balance payload is invalid.',
      ),
      positionsPayload: _requiredMapList(
        json['positions_payload'],
        'The synchronized positions payload is invalid.',
      ),
      ordersPayload: _requiredMapList(
        json['orders_payload'],
        'The synchronized orders payload is invalid.',
      ),
      errorMessage:
          errorMessageValue is String && errorMessageValue.trim().isNotEmpty
          ? errorMessageValue.trim()
          : null,
      syncedAt: _requiredDateTime(
        json['synced_at'],
        'The synchronization date is invalid.',
      ),
      createdAt: _requiredDateTime(
        json['created_at'],
        'The synchronization creation date is invalid.',
      ),
    );
  }
}

int _requiredInt(Object? value, String message) {
  if (value is int) {
    return value;
  }

  throw FormatException(message);
}

double _requiredDouble(Object? value, String message) {
  if (value is num) {
    return value.toDouble();
  }

  throw FormatException(message);
}

String _requiredString(Object? value, String message) {
  if (value is String && value.trim().isNotEmpty) {
    return value.trim();
  }

  throw FormatException(message);
}

DateTime _requiredDateTime(Object? value, String message) {
  if (value is String) {
    final parsed = DateTime.tryParse(value);

    if (parsed != null) {
      return parsed;
    }
  }

  throw FormatException(message);
}

Map<String, dynamic> _requiredMap(Object? value, String message) {
  if (value is Map) {
    return Map<String, dynamic>.unmodifiable(Map<String, dynamic>.from(value));
  }

  throw FormatException(message);
}

List<Map<String, dynamic>> _requiredMapList(Object? value, String message) {
  if (value is! List) {
    throw FormatException(message);
  }

  final result = <Map<String, dynamic>>[];

  for (final entry in value) {
    if (entry is! Map) {
      throw FormatException(message);
    }

    result.add(
      Map<String, dynamic>.unmodifiable(Map<String, dynamic>.from(entry)),
    );
  }

  return List<Map<String, dynamic>>.unmodifiable(result);
}
