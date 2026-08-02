class BackendPortfolio {
  const BackendPortfolio({
    required this.id,
    required this.userId,
    required this.name,
    required this.baseCurrency,
    required this.totalValue,
    required this.profitLoss,
    required this.createdAt,
  });

  final int id;
  final int userId;
  final String name;
  final String baseCurrency;
  final double totalValue;
  final double profitLoss;
  final DateTime createdAt;

  factory BackendPortfolio.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final userId = json['user_id'];
    final name = json['name'];
    final baseCurrency = json['base_currency'];
    final createdAt = json['created_at'];

    if (id is! int ||
        userId is! int ||
        name is! String ||
        name.trim().isEmpty ||
        baseCurrency is! String ||
        baseCurrency.trim().isEmpty ||
        createdAt is! String) {
      throw const FormatException('The portfolio response is invalid.');
    }

    final parsedCreatedAt = DateTime.tryParse(createdAt);

    if (parsedCreatedAt == null) {
      throw const FormatException('The portfolio creation date is invalid.');
    }

    return BackendPortfolio(
      id: id,
      userId: userId,
      name: name.trim(),
      baseCurrency: baseCurrency.trim().toUpperCase(),
      totalValue: _readDouble(
        json['total_value'],
        'The portfolio total value is invalid.',
      ),
      profitLoss: _readDouble(
        json['profit_loss'],
        'The portfolio profit or loss is invalid.',
      ),
      createdAt: parsedCreatedAt,
    );
  }

  BackendPortfolio copyWith({
    String? name,
    String? baseCurrency,
    double? totalValue,
    double? profitLoss,
  }) {
    return BackendPortfolio(
      id: id,
      userId: userId,
      name: name ?? this.name,
      baseCurrency: baseCurrency ?? this.baseCurrency,
      totalValue: totalValue ?? this.totalValue,
      profitLoss: profitLoss ?? this.profitLoss,
      createdAt: createdAt,
    );
  }
}

double _readDouble(Object? value, String message) {
  if (value is num) {
    return value.toDouble();
  }

  throw FormatException(message);
}
