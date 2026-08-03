enum TradingBotStrategyType {
  ruleBased,
  momentum,
  trend,
  meanReversion,
  scalping,
  grid,
  dca,
  arbitrage,
  custom,
}

extension TradingBotStrategyTypeValue on TradingBotStrategyType {
  String get backendValue {
    return switch (this) {
      TradingBotStrategyType.ruleBased => 'RULE_BASED',
      TradingBotStrategyType.momentum => 'MOMENTUM',
      TradingBotStrategyType.trend => 'TREND',
      TradingBotStrategyType.meanReversion => 'MEAN_REVERSION',
      TradingBotStrategyType.scalping => 'SCALPING',
      TradingBotStrategyType.grid => 'GRID',
      TradingBotStrategyType.dca => 'DCA',
      TradingBotStrategyType.arbitrage => 'ARBITRAGE',
      TradingBotStrategyType.custom => 'CUSTOM',
    };
  }
}

enum TradingBotStatus {
  draft,
  stopped,
  starting,
  running,
  paused,
  error,
  archived,
}

extension TradingBotStatusValue on TradingBotStatus {
  String get backendValue {
    return switch (this) {
      TradingBotStatus.draft => 'DRAFT',
      TradingBotStatus.stopped => 'STOPPED',
      TradingBotStatus.starting => 'STARTING',
      TradingBotStatus.running => 'RUNNING',
      TradingBotStatus.paused => 'PAUSED',
      TradingBotStatus.error => 'ERROR',
      TradingBotStatus.archived => 'ARCHIVED',
    };
  }

  bool get isActive {
    return switch (this) {
      TradingBotStatus.starting ||
      TradingBotStatus.running ||
      TradingBotStatus.paused => true,
      _ => false,
    };
  }
}

enum TradingBotCategory { spot, linear, inverse }

extension TradingBotCategoryValue on TradingBotCategory {
  String get backendValue => name;
}

enum TradingBotTimeframe {
  oneMinute,
  threeMinutes,
  fiveMinutes,
  fifteenMinutes,
  thirtyMinutes,
  oneHour,
  twoHours,
  fourHours,
  sixHours,
  twelveHours,
  oneDay,
}

extension TradingBotTimeframeValue on TradingBotTimeframe {
  String get backendValue {
    return switch (this) {
      TradingBotTimeframe.oneMinute => '1m',
      TradingBotTimeframe.threeMinutes => '3m',
      TradingBotTimeframe.fiveMinutes => '5m',
      TradingBotTimeframe.fifteenMinutes => '15m',
      TradingBotTimeframe.thirtyMinutes => '30m',
      TradingBotTimeframe.oneHour => '1h',
      TradingBotTimeframe.twoHours => '2h',
      TradingBotTimeframe.fourHours => '4h',
      TradingBotTimeframe.sixHours => '6h',
      TradingBotTimeframe.twelveHours => '12h',
      TradingBotTimeframe.oneDay => '1d',
    };
  }
}

enum TradingBotLifecycleAction { prepare, start, pause, resume, stop }

extension TradingBotLifecycleActionValue on TradingBotLifecycleAction {
  String get backendValue {
    return switch (this) {
      TradingBotLifecycleAction.prepare => 'PREPARE',
      TradingBotLifecycleAction.start => 'START',
      TradingBotLifecycleAction.pause => 'PAUSE',
      TradingBotLifecycleAction.resume => 'RESUME',
      TradingBotLifecycleAction.stop => 'STOP',
    };
  }

  String get routeValue => name;
}

class BackendTradingBot {
  const BackendTradingBot({
    required this.id,
    required this.userId,
    required this.exchangeAccountId,
    required this.name,
    required this.description,
    required this.strategyType,
    required this.symbol,
    required this.category,
    required this.timeframe,
    required this.status,
    required this.paperTrading,
    required this.dryRun,
    required this.riskPerTradePercent,
    required this.maxPositionValueUsd,
    required this.maxDailyLossPercent,
    required this.maxDrawdownPercent,
    required this.stopLossPercent,
    required this.takeProfitPercent,
    required this.strategyConfig,
    required this.lastError,
    required this.startedAt,
    required this.stoppedAt,
    required this.lastRunAt,
    required this.createdAt,
    required this.updatedAt,
  });

  final int id;
  final int userId;
  final int? exchangeAccountId;
  final String name;
  final String? description;
  final TradingBotStrategyType strategyType;
  final String symbol;
  final TradingBotCategory category;
  final TradingBotTimeframe timeframe;
  final TradingBotStatus status;
  final bool paperTrading;
  final bool dryRun;
  final double riskPerTradePercent;
  final double maxPositionValueUsd;
  final double maxDailyLossPercent;
  final double maxDrawdownPercent;
  final double? stopLossPercent;
  final double? takeProfitPercent;
  final Map<String, dynamic> strategyConfig;
  final String? lastError;
  final DateTime? startedAt;
  final DateTime? stoppedAt;
  final DateTime? lastRunAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory BackendTradingBot.fromJson(Map<String, dynamic> json) {
    return BackendTradingBot(
      id: _readPositiveInt(json, 'id'),
      userId: _readPositiveInt(json, 'user_id'),
      exchangeAccountId: _readNullablePositiveInt(json, 'exchange_account_id'),
      name: _readRequiredString(json, 'name'),
      description: _readNullableString(json, 'description'),
      strategyType: _parseStrategyType(json['strategy_type']),
      symbol: _readRequiredString(json, 'symbol').toUpperCase(),
      category: _parseCategory(json['category']),
      timeframe: _parseTimeframe(json['timeframe']),
      status: _parseStatus(json['status']),
      paperTrading: _readBool(json, 'paper_trading'),
      dryRun: _readBool(json, 'dry_run'),
      riskPerTradePercent: _readPositiveDouble(json, 'risk_per_trade_percent'),
      maxPositionValueUsd: _readPositiveDouble(json, 'max_position_value_usd'),
      maxDailyLossPercent: _readPositiveDouble(json, 'max_daily_loss_percent'),
      maxDrawdownPercent: _readPositiveDouble(json, 'max_drawdown_percent'),
      stopLossPercent: _readNullablePositiveDouble(json, 'stop_loss_percent'),
      takeProfitPercent: _readNullablePositiveDouble(
        json,
        'take_profit_percent',
      ),
      strategyConfig: _readMap(json, 'strategy_config'),
      lastError: _readNullableString(json, 'last_error'),
      startedAt: _readNullableDateTime(json, 'started_at'),
      stoppedAt: _readNullableDateTime(json, 'stopped_at'),
      lastRunAt: _readNullableDateTime(json, 'last_run_at'),
      createdAt: _readDateTime(json, 'created_at'),
      updatedAt: _readDateTime(json, 'updated_at'),
    );
  }
}

class TradingBotCreateRequest {
  const TradingBotCreateRequest({
    required this.name,
    required this.symbol,
    this.exchangeAccountId,
    this.description,
    this.strategyType = TradingBotStrategyType.ruleBased,
    this.category = TradingBotCategory.linear,
    this.timeframe = TradingBotTimeframe.fiveMinutes,
    this.paperTrading = true,
    this.dryRun = true,
    this.riskPerTradePercent = 1,
    this.maxPositionValueUsd = 25,
    this.maxDailyLossPercent = 3,
    this.maxDrawdownPercent = 10,
    this.stopLossPercent,
    this.takeProfitPercent,
    this.strategyConfig = const <String, dynamic>{},
  });

  final int? exchangeAccountId;
  final String name;
  final String? description;
  final TradingBotStrategyType strategyType;
  final String symbol;
  final TradingBotCategory category;
  final TradingBotTimeframe timeframe;
  final bool paperTrading;
  final bool dryRun;
  final double riskPerTradePercent;
  final double maxPositionValueUsd;
  final double maxDailyLossPercent;
  final double maxDrawdownPercent;
  final double? stopLossPercent;
  final double? takeProfitPercent;
  final Map<String, dynamic> strategyConfig;

  Map<String, Object?> toJson() {
    _validateConfiguration(
      exchangeAccountId: exchangeAccountId,
      name: name,
      description: description,
      symbol: symbol,
      paperTrading: paperTrading,
      dryRun: dryRun,
      riskPerTradePercent: riskPerTradePercent,
      maxPositionValueUsd: maxPositionValueUsd,
      maxDailyLossPercent: maxDailyLossPercent,
      maxDrawdownPercent: maxDrawdownPercent,
      stopLossPercent: stopLossPercent,
      takeProfitPercent: takeProfitPercent,
    );

    return <String, Object?>{
      if (exchangeAccountId != null) 'exchange_account_id': exchangeAccountId,
      'name': _normalizeName(name),
      if (description != null)
        'description': _normalizeDescription(description!),
      'strategy_type': strategyType.backendValue,
      'symbol': _normalizeSymbol(symbol),
      'category': category.backendValue,
      'timeframe': timeframe.backendValue,
      'paper_trading': paperTrading,
      'dry_run': dryRun,
      'risk_per_trade_percent': riskPerTradePercent,
      'max_position_value_usd': maxPositionValueUsd,
      'max_daily_loss_percent': maxDailyLossPercent,
      'max_drawdown_percent': maxDrawdownPercent,
      if (stopLossPercent != null) 'stop_loss_percent': stopLossPercent,
      if (takeProfitPercent != null) 'take_profit_percent': takeProfitPercent,
      'strategy_config': Map<String, dynamic>.from(strategyConfig),
    };
  }
}

class TradingBotUpdateRequest {
  const TradingBotUpdateRequest({
    this.exchangeAccountId,
    this.name,
    this.description,
    this.strategyType,
    this.symbol,
    this.category,
    this.timeframe,
    this.paperTrading,
    this.dryRun,
    this.riskPerTradePercent,
    this.maxPositionValueUsd,
    this.maxDailyLossPercent,
    this.maxDrawdownPercent,
    this.stopLossPercent,
    this.takeProfitPercent,
    this.strategyConfig,
  });

  final int? exchangeAccountId;
  final String? name;
  final String? description;
  final TradingBotStrategyType? strategyType;
  final String? symbol;
  final TradingBotCategory? category;
  final TradingBotTimeframe? timeframe;
  final bool? paperTrading;
  final bool? dryRun;
  final double? riskPerTradePercent;
  final double? maxPositionValueUsd;
  final double? maxDailyLossPercent;
  final double? maxDrawdownPercent;
  final double? stopLossPercent;
  final double? takeProfitPercent;
  final Map<String, dynamic>? strategyConfig;

  bool get hasChanges {
    return exchangeAccountId != null ||
        name != null ||
        description != null ||
        strategyType != null ||
        symbol != null ||
        category != null ||
        timeframe != null ||
        paperTrading != null ||
        dryRun != null ||
        riskPerTradePercent != null ||
        maxPositionValueUsd != null ||
        maxDailyLossPercent != null ||
        maxDrawdownPercent != null ||
        stopLossPercent != null ||
        takeProfitPercent != null ||
        strategyConfig != null;
  }

  Map<String, Object?> toJson() {
    if (!hasChanges) {
      throw const FormatException(
        'At least one trading-bot field must be supplied.',
      );
    }

    if (exchangeAccountId != null && exchangeAccountId! <= 0) {
      throw const FormatException('The exchange-account ID must be positive.');
    }

    if (name != null) {
      _normalizeName(name!);
    }

    if (description != null) {
      _normalizeDescription(description!);
    }

    if (symbol != null) {
      _normalizeSymbol(symbol!);
    }

    _validateOptionalPercentage(
      riskPerTradePercent,
      'Risk per trade',
      maximum: 100,
    );
    _validateOptionalPositive(maxPositionValueUsd, 'Maximum position value');
    _validateOptionalPercentage(
      maxDailyLossPercent,
      'Maximum daily loss',
      maximum: 100,
    );
    _validateOptionalPercentage(
      maxDrawdownPercent,
      'Maximum drawdown',
      maximum: 100,
    );
    _validateOptionalPercentage(stopLossPercent, 'Stop loss', maximum: 100);
    _validateOptionalPercentage(
      takeProfitPercent,
      'Take profit',
      maximum: 1000,
    );

    if (paperTrading == false && dryRun == false) {
      throw const FormatException(
        'At least paper trading or dry run must remain enabled.',
      );
    }

    return <String, Object?>{
      if (exchangeAccountId != null) 'exchange_account_id': exchangeAccountId,
      if (name != null) 'name': _normalizeName(name!),
      if (description != null)
        'description': _normalizeDescription(description!),
      if (strategyType != null) 'strategy_type': strategyType!.backendValue,
      if (symbol != null) 'symbol': _normalizeSymbol(symbol!),
      if (category != null) 'category': category!.backendValue,
      if (timeframe != null) 'timeframe': timeframe!.backendValue,
      if (paperTrading != null) 'paper_trading': paperTrading,
      if (dryRun != null) 'dry_run': dryRun,
      if (riskPerTradePercent != null)
        'risk_per_trade_percent': riskPerTradePercent,
      if (maxPositionValueUsd != null)
        'max_position_value_usd': maxPositionValueUsd,
      if (maxDailyLossPercent != null)
        'max_daily_loss_percent': maxDailyLossPercent,
      if (maxDrawdownPercent != null)
        'max_drawdown_percent': maxDrawdownPercent,
      if (stopLossPercent != null) 'stop_loss_percent': stopLossPercent,
      if (takeProfitPercent != null) 'take_profit_percent': takeProfitPercent,
      if (strategyConfig != null)
        'strategy_config': Map<String, dynamic>.from(strategyConfig!),
    };
  }
}

class TradingBotLifecycleResult {
  const TradingBotLifecycleResult({
    required this.action,
    required this.previousStatus,
    required this.status,
    required this.changed,
    required this.bot,
  });

  final TradingBotLifecycleAction action;
  final TradingBotStatus previousStatus;
  final TradingBotStatus status;
  final bool changed;
  final BackendTradingBot bot;

  factory TradingBotLifecycleResult.fromJson(Map<String, dynamic> json) {
    final bot = json['bot'];

    if (bot is! Map) {
      throw const FormatException(
        'The lifecycle result contains an invalid bot.',
      );
    }

    return TradingBotLifecycleResult(
      action: _parseLifecycleAction(json['action']),
      previousStatus: _parseStatus(json['previous_status']),
      status: _parseStatus(json['status']),
      changed: _readBool(json, 'changed'),
      bot: BackendTradingBot.fromJson(Map<String, dynamic>.from(bot)),
    );
  }
}

TradingBotStrategyType _parseStrategyType(Object? value) {
  final normalized = _normalizedEnum(value);

  return switch (normalized) {
    'RULE_BASED' => TradingBotStrategyType.ruleBased,
    'MOMENTUM' => TradingBotStrategyType.momentum,
    'TREND' => TradingBotStrategyType.trend,
    'MEAN_REVERSION' => TradingBotStrategyType.meanReversion,
    'SCALPING' => TradingBotStrategyType.scalping,
    'GRID' => TradingBotStrategyType.grid,
    'DCA' => TradingBotStrategyType.dca,
    'ARBITRAGE' => TradingBotStrategyType.arbitrage,
    'CUSTOM' => TradingBotStrategyType.custom,
    _ => throw FormatException('Unsupported trading-bot strategy: $value'),
  };
}

TradingBotStatus _parseStatus(Object? value) {
  final normalized = _normalizedEnum(value);

  return switch (normalized) {
    'DRAFT' => TradingBotStatus.draft,
    'STOPPED' => TradingBotStatus.stopped,
    'STARTING' => TradingBotStatus.starting,
    'RUNNING' => TradingBotStatus.running,
    'PAUSED' => TradingBotStatus.paused,
    'ERROR' => TradingBotStatus.error,
    'ARCHIVED' => TradingBotStatus.archived,
    _ => throw FormatException('Unsupported trading-bot status: $value'),
  };
}

TradingBotCategory _parseCategory(Object? value) {
  final normalized = _normalizedEnum(value).toLowerCase();

  return switch (normalized) {
    'spot' => TradingBotCategory.spot,
    'linear' => TradingBotCategory.linear,
    'inverse' => TradingBotCategory.inverse,
    _ => throw FormatException('Unsupported trading-bot category: $value'),
  };
}

TradingBotTimeframe _parseTimeframe(Object? value) {
  final normalized = value is String ? value.trim() : '';

  return switch (normalized) {
    '1m' => TradingBotTimeframe.oneMinute,
    '3m' => TradingBotTimeframe.threeMinutes,
    '5m' => TradingBotTimeframe.fiveMinutes,
    '15m' => TradingBotTimeframe.fifteenMinutes,
    '30m' => TradingBotTimeframe.thirtyMinutes,
    '1h' => TradingBotTimeframe.oneHour,
    '2h' => TradingBotTimeframe.twoHours,
    '4h' => TradingBotTimeframe.fourHours,
    '6h' => TradingBotTimeframe.sixHours,
    '12h' => TradingBotTimeframe.twelveHours,
    '1d' => TradingBotTimeframe.oneDay,
    _ => throw FormatException('Unsupported trading-bot timeframe: $value'),
  };
}

TradingBotLifecycleAction _parseLifecycleAction(Object? value) {
  final normalized = _normalizedEnum(value);

  return switch (normalized) {
    'PREPARE' => TradingBotLifecycleAction.prepare,
    'START' => TradingBotLifecycleAction.start,
    'PAUSE' => TradingBotLifecycleAction.pause,
    'RESUME' => TradingBotLifecycleAction.resume,
    'STOP' => TradingBotLifecycleAction.stop,
    _ => throw FormatException('Unsupported lifecycle action: $value'),
  };
}

String _normalizedEnum(Object? value) {
  if (value is! String || value.trim().isEmpty) {
    throw const FormatException('A backend enum value is missing.');
  }

  return value.trim().toUpperCase();
}

int _readPositiveInt(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is int && value > 0) {
    return value;
  }

  if (value is num && value.isFinite && value > 0 && value.toInt() == value) {
    return value.toInt();
  }

  throw FormatException('$key must be a positive integer.');
}

int? _readNullablePositiveInt(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value == null) {
    return null;
  }

  return _readPositiveInt(json, key);
}

double _readPositiveDouble(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is num && value.isFinite && value > 0) {
    return value.toDouble();
  }

  throw FormatException('$key must be a positive number.');
}

double? _readNullablePositiveDouble(Map<String, dynamic> json, String key) {
  if (json[key] == null) {
    return null;
  }

  return _readPositiveDouble(json, key);
}

bool _readBool(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is bool) {
    return value;
  }

  throw FormatException('$key must be a boolean.');
}

String _readRequiredString(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is String && value.trim().isNotEmpty) {
    return value.trim();
  }

  throw FormatException('$key must be a non-empty string.');
}

String? _readNullableString(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value == null) {
    return null;
  }

  if (value is! String) {
    throw FormatException('$key must be a string or null.');
  }

  final normalized = value.trim();
  return normalized.isEmpty ? null : normalized;
}

DateTime _readDateTime(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is! String) {
    throw FormatException('$key must be a date-time string.');
  }

  final parsed = DateTime.tryParse(value);

  if (parsed == null) {
    throw FormatException('$key is not a valid date-time.');
  }

  return parsed.toUtc();
}

DateTime? _readNullableDateTime(Map<String, dynamic> json, String key) {
  if (json[key] == null) {
    return null;
  }

  return _readDateTime(json, key);
}

Map<String, dynamic> _readMap(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is! Map) {
    throw FormatException('$key must be an object.');
  }

  return Map<String, dynamic>.unmodifiable(Map<String, dynamic>.from(value));
}

String _normalizeName(String value) {
  final normalized = value.trim().split(RegExp(r'\s+')).join(' ');

  if (normalized.length < 2 || normalized.length > 150) {
    throw const FormatException(
      'The trading-bot name must contain 2 to 150 characters.',
    );
  }

  return normalized;
}

String _normalizeDescription(String value) {
  final normalized = value.trim();

  if (normalized.length > 2000) {
    throw const FormatException(
      'The description cannot exceed 2000 characters.',
    );
  }

  return normalized;
}

String _normalizeSymbol(String value) {
  final normalized = value.trim().toUpperCase();

  if (normalized.length < 2 || normalized.length > 30) {
    throw const FormatException(
      'The trading symbol must contain 2 to 30 characters.',
    );
  }

  return normalized;
}

void _validateConfiguration({
  required int? exchangeAccountId,
  required String name,
  required String? description,
  required String symbol,
  required bool paperTrading,
  required bool dryRun,
  required double riskPerTradePercent,
  required double maxPositionValueUsd,
  required double maxDailyLossPercent,
  required double maxDrawdownPercent,
  required double? stopLossPercent,
  required double? takeProfitPercent,
}) {
  if (exchangeAccountId != null && exchangeAccountId <= 0) {
    throw const FormatException('The exchange-account ID must be positive.');
  }

  _normalizeName(name);
  _normalizeSymbol(symbol);

  if (description != null) {
    _normalizeDescription(description);
  }

  _validatePercentage(riskPerTradePercent, 'Risk per trade', maximum: 100);
  _validatePositive(maxPositionValueUsd, 'Maximum position value');
  _validatePercentage(maxDailyLossPercent, 'Maximum daily loss', maximum: 100);
  _validatePercentage(maxDrawdownPercent, 'Maximum drawdown', maximum: 100);

  if (stopLossPercent != null) {
    _validatePercentage(stopLossPercent, 'Stop loss', maximum: 100);
  }

  if (takeProfitPercent != null) {
    _validatePercentage(takeProfitPercent, 'Take profit', maximum: 1000);
  }

  if (!paperTrading && !dryRun) {
    throw const FormatException(
      'At least paper trading or dry run must remain enabled.',
    );
  }

  if (riskPerTradePercent > maxDailyLossPercent) {
    throw const FormatException(
      'Risk per trade cannot exceed the maximum daily loss.',
    );
  }

  if (maxDailyLossPercent > maxDrawdownPercent) {
    throw const FormatException(
      'Maximum daily loss cannot exceed maximum drawdown.',
    );
  }
}

void _validatePositive(double value, String label) {
  if (!value.isFinite || value <= 0) {
    throw FormatException('$label must be greater than zero.');
  }
}

void _validatePercentage(
  double value,
  String label, {
  required double maximum,
}) {
  _validatePositive(value, label);

  if (value > maximum) {
    throw FormatException('$label cannot exceed $maximum.');
  }
}

void _validateOptionalPositive(double? value, String label) {
  if (value != null) {
    _validatePositive(value, label);
  }
}

void _validateOptionalPercentage(
  double? value,
  String label, {
  required double maximum,
}) {
  if (value != null) {
    _validatePercentage(value, label, maximum: maximum);
  }
}
