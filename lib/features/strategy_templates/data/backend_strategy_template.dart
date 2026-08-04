import '../../bots/data/backend_trading_bot.dart';

enum StrategyTemplateVisibility { privateTemplate, publicTemplate }

extension StrategyTemplateVisibilityValue on StrategyTemplateVisibility {
  String get backendValue {
    return switch (this) {
      StrategyTemplateVisibility.privateTemplate => 'PRIVATE',
      StrategyTemplateVisibility.publicTemplate => 'PUBLIC',
    };
  }

  static StrategyTemplateVisibility fromBackendValue(Object? value) {
    return switch (value) {
      'PRIVATE' => StrategyTemplateVisibility.privateTemplate,
      'PUBLIC' => StrategyTemplateVisibility.publicTemplate,
      _ => throw const FormatException(
        'The strategy-template visibility is invalid.',
      ),
    };
  }
}

enum StrategyTemplateStatus { draft, published, archived }

extension StrategyTemplateStatusValue on StrategyTemplateStatus {
  String get backendValue {
    return switch (this) {
      StrategyTemplateStatus.draft => 'DRAFT',
      StrategyTemplateStatus.published => 'PUBLISHED',
      StrategyTemplateStatus.archived => 'ARCHIVED',
    };
  }

  static StrategyTemplateStatus fromBackendValue(Object? value) {
    return switch (value) {
      'DRAFT' => StrategyTemplateStatus.draft,
      'PUBLISHED' => StrategyTemplateStatus.published,
      'ARCHIVED' => StrategyTemplateStatus.archived,
      _ => throw const FormatException(
        'The strategy-template status is invalid.',
      ),
    };
  }
}

enum StrategyTemplateAction { publish, unpublish, archive, restore }

extension StrategyTemplateActionValue on StrategyTemplateAction {
  String get backendValue {
    return switch (this) {
      StrategyTemplateAction.publish => 'PUBLISH',
      StrategyTemplateAction.unpublish => 'UNPUBLISH',
      StrategyTemplateAction.archive => 'ARCHIVE',
      StrategyTemplateAction.restore => 'RESTORE',
    };
  }

  String get routeValue {
    return switch (this) {
      StrategyTemplateAction.publish => 'publish',
      StrategyTemplateAction.unpublish => 'unpublish',
      StrategyTemplateAction.archive => 'archive',
      StrategyTemplateAction.restore => 'restore',
    };
  }

  static StrategyTemplateAction fromBackendValue(Object? value) {
    return switch (value) {
      'PUBLISH' => StrategyTemplateAction.publish,
      'UNPUBLISH' => StrategyTemplateAction.unpublish,
      'ARCHIVE' => StrategyTemplateAction.archive,
      'RESTORE' => StrategyTemplateAction.restore,
      _ => throw const FormatException(
        'The strategy-template action is invalid.',
      ),
    };
  }
}

class BackendStrategyTemplate {
  const BackendStrategyTemplate({
    required this.id,
    required this.userId,
    required this.name,
    required this.strategyType,
    required this.symbol,
    required this.category,
    required this.timeframe,
    required this.visibility,
    required this.paperTrading,
    required this.dryRun,
    required this.riskPerTradePercent,
    required this.maxPositionValueUsd,
    required this.maxDailyLossPercent,
    required this.maxDrawdownPercent,
    required this.strategyConfig,
    required this.status,
    required this.version,
    required this.createdAt,
    required this.updatedAt,
    this.description,
    this.stopLossPercent,
    this.takeProfitPercent,
    this.publishedAt,
    this.archivedAt,
  });

  final int id;
  final int userId;
  final String name;
  final String? description;
  final TradingBotStrategyType strategyType;
  final String symbol;
  final TradingBotCategory category;
  final TradingBotTimeframe timeframe;
  final StrategyTemplateVisibility visibility;
  final bool paperTrading;
  final bool dryRun;
  final double riskPerTradePercent;
  final double maxPositionValueUsd;
  final double maxDailyLossPercent;
  final double maxDrawdownPercent;
  final double? stopLossPercent;
  final double? takeProfitPercent;
  final Map<String, dynamic> strategyConfig;
  final StrategyTemplateStatus status;
  final int version;
  final DateTime? publishedAt;
  final DateTime? archivedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory BackendStrategyTemplate.fromJson(Map<String, dynamic> json) {
    return BackendStrategyTemplate(
      id: _requiredInt(json, 'id'),
      userId: _requiredInt(json, 'user_id'),
      name: _requiredString(json, 'name'),
      description: _optionalString(json['description']),
      strategyType: _parseStrategyType(json['strategy_type']),
      symbol: _requiredString(json, 'symbol'),
      category: _parseCategory(json['category']),
      timeframe: _parseTimeframe(json['timeframe']),
      visibility: StrategyTemplateVisibilityValue.fromBackendValue(
        json['visibility'],
      ),
      paperTrading: _requiredBool(json, 'paper_trading'),
      dryRun: _requiredBool(json, 'dry_run'),
      riskPerTradePercent: _requiredDouble(json, 'risk_per_trade_percent'),
      maxPositionValueUsd: _requiredDouble(json, 'max_position_value_usd'),
      maxDailyLossPercent: _requiredDouble(json, 'max_daily_loss_percent'),
      maxDrawdownPercent: _requiredDouble(json, 'max_drawdown_percent'),
      stopLossPercent: _optionalDouble(json['stop_loss_percent']),
      takeProfitPercent: _optionalDouble(json['take_profit_percent']),
      strategyConfig: _requiredMap(json, 'strategy_config'),
      status: StrategyTemplateStatusValue.fromBackendValue(json['status']),
      version: _requiredInt(json, 'version'),
      publishedAt: _optionalDateTime(json['published_at']),
      archivedAt: _optionalDateTime(json['archived_at']),
      createdAt: _requiredDateTime(json, 'created_at'),
      updatedAt: _requiredDateTime(json, 'updated_at'),
    );
  }
}

class StrategyTemplateCreateRequest {
  const StrategyTemplateCreateRequest({
    required this.name,
    required this.symbol,
    this.description,
    this.strategyType = TradingBotStrategyType.ruleBased,
    this.category = TradingBotCategory.linear,
    this.timeframe = TradingBotTimeframe.fiveMinutes,
    this.visibility = StrategyTemplateVisibility.privateTemplate,
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

  final String name;
  final String? description;
  final TradingBotStrategyType strategyType;
  final String symbol;
  final TradingBotCategory category;
  final TradingBotTimeframe timeframe;
  final StrategyTemplateVisibility visibility;
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
      'name': _normalizeName(name),
      if (description != null)
        'description': _normalizeDescription(description!),
      'strategy_type': strategyType.backendValue,
      'symbol': _normalizeSymbol(symbol),
      'category': category.backendValue,
      'timeframe': timeframe.backendValue,
      'visibility': visibility.backendValue,
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

class StrategyTemplateUpdateRequest {
  const StrategyTemplateUpdateRequest({
    this.name,
    this.description,
    this.strategyType,
    this.symbol,
    this.category,
    this.timeframe,
    this.visibility,
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

  final String? name;
  final String? description;
  final TradingBotStrategyType? strategyType;
  final String? symbol;
  final TradingBotCategory? category;
  final TradingBotTimeframe? timeframe;
  final StrategyTemplateVisibility? visibility;
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
    return name != null ||
        description != null ||
        strategyType != null ||
        symbol != null ||
        category != null ||
        timeframe != null ||
        visibility != null ||
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
        'At least one strategy-template field must be supplied.',
      );
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

    if (paperTrading == false && dryRun == false) {
      throw const FormatException(
        'Paper trading or dry run must remain enabled.',
      );
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

    if (riskPerTradePercent != null &&
        maxDailyLossPercent != null &&
        riskPerTradePercent! > maxDailyLossPercent!) {
      throw const FormatException(
        'Risk per trade cannot exceed maximum daily loss.',
      );
    }

    if (maxDailyLossPercent != null &&
        maxDrawdownPercent != null &&
        maxDailyLossPercent! > maxDrawdownPercent!) {
      throw const FormatException(
        'Maximum daily loss cannot exceed maximum drawdown.',
      );
    }

    return <String, Object?>{
      if (name != null) 'name': _normalizeName(name!),
      if (description != null)
        'description': _normalizeDescription(description!),
      if (strategyType != null) 'strategy_type': strategyType!.backendValue,
      if (symbol != null) 'symbol': _normalizeSymbol(symbol!),
      if (category != null) 'category': category!.backendValue,
      if (timeframe != null) 'timeframe': timeframe!.backendValue,
      if (visibility != null) 'visibility': visibility!.backendValue,
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

class StrategyTemplateActionResult {
  const StrategyTemplateActionResult({
    required this.action,
    required this.previousStatus,
    required this.status,
    required this.changed,
    required this.template,
  });

  final StrategyTemplateAction action;
  final StrategyTemplateStatus previousStatus;
  final StrategyTemplateStatus status;
  final bool changed;
  final BackendStrategyTemplate template;

  factory StrategyTemplateActionResult.fromJson(Map<String, dynamic> json) {
    final templateValue = json['template'];

    if (templateValue is! Map) {
      throw const FormatException(
        'The strategy-template action result is invalid.',
      );
    }

    return StrategyTemplateActionResult(
      action: StrategyTemplateActionValue.fromBackendValue(json['action']),
      previousStatus: StrategyTemplateStatusValue.fromBackendValue(
        json['previous_status'],
      ),
      status: StrategyTemplateStatusValue.fromBackendValue(json['status']),
      changed: _requiredBool(json, 'changed'),
      template: BackendStrategyTemplate.fromJson(
        Map<String, dynamic>.from(templateValue),
      ),
    );
  }
}

class StrategyTemplateBotCreateRequest {
  const StrategyTemplateBotCreateRequest({
    required this.name,
    this.exchangeAccountId,
    this.description,
  });

  final int? exchangeAccountId;
  final String name;
  final String? description;

  Map<String, Object?> toJson() {
    if (exchangeAccountId != null && exchangeAccountId! <= 0) {
      throw const FormatException('The exchange-account ID must be positive.');
    }

    return <String, Object?>{
      if (exchangeAccountId != null) 'exchange_account_id': exchangeAccountId,
      'name': _normalizeName(name),
      if (description != null)
        'description': _normalizeDescription(description!),
    };
  }
}

void _validateConfiguration({
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
  _normalizeName(name);

  if (description != null) {
    _normalizeDescription(description);
  }

  _normalizeSymbol(symbol);

  if (!paperTrading && !dryRun) {
    throw const FormatException(
      'Paper trading or dry run must remain enabled.',
    );
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

  if (riskPerTradePercent > maxDailyLossPercent) {
    throw const FormatException(
      'Risk per trade cannot exceed maximum daily loss.',
    );
  }

  if (maxDailyLossPercent > maxDrawdownPercent) {
    throw const FormatException(
      'Maximum daily loss cannot exceed maximum drawdown.',
    );
  }
}

String _normalizeName(String value) {
  final normalized = value.trim().split(RegExp(r'\s+')).join(' ');

  if (normalized.length < 2 || normalized.length > 150) {
    throw const FormatException(
      'The strategy-template name must contain 2 to 150 characters.',
    );
  }

  return normalized;
}

String? _normalizeDescription(String value) {
  final normalized = value.trim();

  if (normalized.length > 2000) {
    throw const FormatException(
      'The description cannot exceed 2000 characters.',
    );
  }

  return normalized.isEmpty ? null : normalized;
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

void _validatePositive(double value, String label) {
  if (!value.isFinite || value <= 0) {
    throw FormatException('$label must be positive.');
  }
}

void _validateOptionalPositive(double? value, String label) {
  if (value != null) {
    _validatePositive(value, label);
  }
}

void _validatePercentage(
  double value,
  String label, {
  required double maximum,
}) {
  if (!value.isFinite || value <= 0 || value > maximum) {
    throw FormatException(
      '$label must be greater than zero and no more than $maximum.',
    );
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

int _requiredInt(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is int) {
    return value;
  }

  throw FormatException('$key must be an integer.');
}

String _requiredString(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is String && value.trim().isNotEmpty) {
    return value;
  }

  throw FormatException('$key must be a string.');
}

String? _optionalString(Object? value) {
  if (value == null) {
    return null;
  }

  if (value is String) {
    return value;
  }

  throw const FormatException('An optional string value is invalid.');
}

bool _requiredBool(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is bool) {
    return value;
  }

  throw FormatException('$key must be a boolean.');
}

double _requiredDouble(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is num) {
    return value.toDouble();
  }

  throw FormatException('$key must be numeric.');
}

double? _optionalDouble(Object? value) {
  if (value == null) {
    return null;
  }

  if (value is num) {
    return value.toDouble();
  }

  throw const FormatException('An optional numeric value is invalid.');
}

Map<String, dynamic> _requiredMap(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is Map) {
    return Map<String, dynamic>.from(value);
  }

  throw FormatException('$key must be an object.');
}

DateTime _requiredDateTime(Map<String, dynamic> json, String key) {
  final value = json[key];

  if (value is! String) {
    throw FormatException('$key must be a timestamp.');
  }

  return DateTime.tryParse(value) ??
      (throw FormatException('$key must be a valid timestamp.'));
}

DateTime? _optionalDateTime(Object? value) {
  if (value == null) {
    return null;
  }

  if (value is! String) {
    throw const FormatException('An optional timestamp is invalid.');
  }

  return DateTime.tryParse(value) ??
      (throw const FormatException('An optional timestamp is invalid.'));
}

TradingBotStrategyType _parseStrategyType(Object? value) {
  for (final item in TradingBotStrategyType.values) {
    if (item.backendValue == value) {
      return item;
    }
  }

  throw const FormatException('The strategy type is invalid.');
}

TradingBotCategory _parseCategory(Object? value) {
  for (final item in TradingBotCategory.values) {
    if (item.backendValue == value) {
      return item;
    }
  }

  throw const FormatException('The trading category is invalid.');
}

TradingBotTimeframe _parseTimeframe(Object? value) {
  for (final item in TradingBotTimeframe.values) {
    if (item.backendValue == value) {
      return item;
    }
  }

  throw const FormatException('The trading timeframe is invalid.');
}
