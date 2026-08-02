class BackendWatchlistItem {
  const BackendWatchlistItem({
    required this.id,
    required this.userId,
    required this.symbol,
    required this.exchange,
    required this.createdAt,
  });

  final int id;
  final int userId;
  final String symbol;
  final String exchange;
  final DateTime createdAt;

  String get baseAssetSymbol {
    return WatchlistSymbolMapper.baseAssetFromPair(symbol);
  }

  factory BackendWatchlistItem.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final userId = json['user_id'];
    final symbol = json['symbol'];
    final exchange = json['exchange'];
    final createdAt = json['created_at'];

    if (id is! int || id <= 0) {
      throw const FormatException('The watchlist item ID is invalid.');
    }

    if (userId is! int || userId <= 0) {
      throw const FormatException('The watchlist user ID is invalid.');
    }

    if (symbol is! String || symbol.trim().length < 2) {
      throw const FormatException('The watchlist symbol is invalid.');
    }

    if (exchange is! String || exchange.trim().length < 2) {
      throw const FormatException('The watchlist exchange is invalid.');
    }

    if (createdAt is! String) {
      throw const FormatException('The watchlist creation time is invalid.');
    }

    final parsedCreatedAt = DateTime.tryParse(createdAt);

    if (parsedCreatedAt == null) {
      throw const FormatException('The watchlist creation time is invalid.');
    }

    return BackendWatchlistItem(
      id: id,
      userId: userId,
      symbol: symbol.trim().toUpperCase(),
      exchange: exchange.trim().toUpperCase(),
      createdAt: parsedCreatedAt.toUtc(),
    );
  }
}

class WatchlistSymbolMapper {
  const WatchlistSymbolMapper._();

  static const String defaultExchange = 'BYBIT';
  static const String quoteAsset = 'USDT';

  static String toUsdtPair(String assetSymbol) {
    final normalized = assetSymbol.trim().toUpperCase();

    if (normalized.length < 2) {
      throw const FormatException('The asset symbol is invalid.');
    }

    if (normalized.endsWith(quoteAsset)) {
      return normalized;
    }

    return '$normalized$quoteAsset';
  }

  static String baseAssetFromPair(String tradingSymbol) {
    final normalized = tradingSymbol.trim().toUpperCase();

    if (normalized.endsWith(quoteAsset) &&
        normalized.length > quoteAsset.length) {
      return normalized.substring(0, normalized.length - quoteAsset.length);
    }

    return normalized;
  }

  static String normalizeExchange(String exchange) {
    final normalized = exchange.trim().toUpperCase();

    if (normalized.length < 2) {
      throw const FormatException('The exchange is invalid.');
    }

    return normalized;
  }
}
