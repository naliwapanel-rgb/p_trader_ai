enum BackendPriceAlertCondition {
  above('PRICE_ABOVE'),
  below('PRICE_BELOW');

  const BackendPriceAlertCondition(this.backendValue);

  final String backendValue;

  String get label {
    switch (this) {
      case BackendPriceAlertCondition.above:
        return 'Price Above';
      case BackendPriceAlertCondition.below:
        return 'Price Below';
    }
  }

  static BackendPriceAlertCondition fromBackendValue(String value) {
    switch (value.trim().toUpperCase()) {
      case 'PRICE_ABOVE':
      case 'ABOVE':
        return BackendPriceAlertCondition.above;
      case 'PRICE_BELOW':
      case 'BELOW':
        return BackendPriceAlertCondition.below;
      default:
        throw FormatException('Unsupported price-alert type: $value');
    }
  }
}

class PriceAlertSymbolMapper {
  const PriceAlertSymbolMapper._();

  static const String defaultExchange = 'BYBIT';
  static const String quoteAsset = 'USDT';

  static String toTradingPair(String value) {
    var normalized = value
        .trim()
        .toUpperCase()
        .replaceAll('/', '')
        .replaceAll('-', '')
        .replaceAll('_', '')
        .replaceAll(' ', '');

    if (normalized.endsWith(quoteAsset)) {
      normalized = normalized.substring(
        0,
        normalized.length - quoteAsset.length,
      );
    }

    if (normalized.length < 2) {
      throw const FormatException('A valid base asset symbol is required.');
    }

    final pair = '$normalized$quoteAsset';

    if (pair.length > 30) {
      throw const FormatException('The trading symbol is too long.');
    }

    return pair;
  }

  static String toBaseAssetSymbol(String value) {
    final pair = toTradingPair(value);

    return pair.substring(0, pair.length - quoteAsset.length);
  }
}

class BackendPriceAlert {
  const BackendPriceAlert({
    required this.id,
    required this.userId,
    required this.symbol,
    required this.exchange,
    required this.condition,
    required this.targetPrice,
    required this.isEnabled,
    required this.triggered,
    required this.createdAt,
  });

  final int id;
  final int userId;
  final String symbol;
  final String exchange;
  final BackendPriceAlertCondition condition;
  final double targetPrice;
  final bool isEnabled;
  final bool triggered;
  final DateTime createdAt;

  String get baseAssetSymbol {
    return PriceAlertSymbolMapper.toBaseAssetSymbol(symbol);
  }

  factory BackendPriceAlert.fromJson(Map<String, dynamic> json) {
    final id = _readPositiveInt(json, 'id');
    final userId = _readPositiveInt(json, 'user_id');
    final symbol = _readNonEmptyString(json, 'symbol');
    final exchange = _readNonEmptyString(json, 'exchange');
    final alertType = _readNonEmptyString(json, 'alert_type');
    final targetPrice = _readPositiveDouble(json, 'target_value');
    final isEnabled = _readBool(json, 'is_enabled');
    final triggered = _readBool(json, 'triggered');
    final createdAt = _readDateTime(json, 'created_at');

    return BackendPriceAlert(
      id: id,
      userId: userId,
      symbol: symbol.toUpperCase(),
      exchange: exchange.toUpperCase(),
      condition: BackendPriceAlertCondition.fromBackendValue(alertType),
      targetPrice: targetPrice,
      isEnabled: isEnabled,
      triggered: triggered,
      createdAt: createdAt,
    );
  }

  BackendPriceAlert copyWith({
    int? id,
    int? userId,
    String? symbol,
    String? exchange,
    BackendPriceAlertCondition? condition,
    double? targetPrice,
    bool? isEnabled,
    bool? triggered,
    DateTime? createdAt,
  }) {
    return BackendPriceAlert(
      id: id ?? this.id,
      userId: userId ?? this.userId,
      symbol: symbol ?? this.symbol,
      exchange: exchange ?? this.exchange,
      condition: condition ?? this.condition,
      targetPrice: targetPrice ?? this.targetPrice,
      isEnabled: isEnabled ?? this.isEnabled,
      triggered: triggered ?? this.triggered,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  static int _readPositiveInt(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is! num || value.toInt() <= 0) {
      throw FormatException('The backend price-alert field "$key" is invalid.');
    }

    return value.toInt();
  }

  static String _readNonEmptyString(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is! String || value.trim().isEmpty) {
      throw FormatException('The backend price-alert field "$key" is invalid.');
    }

    return value.trim();
  }

  static double _readPositiveDouble(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is! num) {
      throw FormatException('The backend price-alert field "$key" is invalid.');
    }

    final parsed = value.toDouble();

    if (!parsed.isFinite || parsed <= 0) {
      throw FormatException('The backend price-alert field "$key" is invalid.');
    }

    return parsed;
  }

  static bool _readBool(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is! bool) {
      throw FormatException('The backend price-alert field "$key" is invalid.');
    }

    return value;
  }

  static DateTime _readDateTime(Map<String, dynamic> json, String key) {
    final value = json[key];

    if (value is DateTime) {
      return value.toUtc();
    }

    if (value is! String) {
      throw FormatException('The backend price-alert field "$key" is invalid.');
    }

    final parsed = DateTime.tryParse(value);

    if (parsed == null) {
      throw FormatException('The backend price-alert field "$key" is invalid.');
    }

    return parsed.toUtc();
  }
}
