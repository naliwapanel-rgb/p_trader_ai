class ExchangeAccount {
  const ExchangeAccount({
    required this.id,
    required this.userId,
    required this.exchangeName,
    required this.accountName,
    required this.isTestnet,
    required this.isActive,
    required this.createdAt,
  });

  final int id;
  final int userId;
  final String exchangeName;
  final String accountName;
  final bool isTestnet;
  final bool isActive;
  final DateTime createdAt;

  String get displayExchange {
    return switch (exchangeName.toUpperCase()) {
      'BYBIT' => 'Bybit',
      'BINANCE' => 'Binance',
      'MEXC' => 'MEXC',
      'GATEIO' => 'Gate.io',
      _ => exchangeName,
    };
  }

  factory ExchangeAccount.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final userId = json['user_id'];
    final exchangeName = json['exchange_name'];
    final accountName = json['account_name'];
    final isTestnet = json['is_testnet'];
    final isActive = json['is_active'];
    final createdAt = json['created_at'];

    if (id is! int ||
        userId is! int ||
        exchangeName is! String ||
        exchangeName.trim().isEmpty ||
        accountName is! String ||
        accountName.trim().isEmpty ||
        isTestnet is! bool ||
        isActive is! bool ||
        createdAt is! String) {
      throw const FormatException('The exchange account response is invalid.');
    }

    final parsedCreatedAt = DateTime.tryParse(createdAt);

    if (parsedCreatedAt == null) {
      throw const FormatException(
        'The exchange account creation date is invalid.',
      );
    }

    return ExchangeAccount(
      id: id,
      userId: userId,
      exchangeName: exchangeName.trim().toUpperCase(),
      accountName: accountName.trim(),
      isTestnet: isTestnet,
      isActive: isActive,
      createdAt: parsedCreatedAt,
    );
  }
}
