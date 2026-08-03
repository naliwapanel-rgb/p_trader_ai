import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';

void main() {
  group('BackendTradingBot', () {
    test('parses the complete backend response', () {
      final bot = BackendTradingBot.fromJson(_botJson(status: 'RUNNING'));

      expect(bot.id, 10);
      expect(bot.userId, 7);
      expect(bot.exchangeAccountId, 3);
      expect(bot.name, 'Lifecycle Bot');
      expect(bot.strategyType, TradingBotStrategyType.momentum);
      expect(bot.symbol, 'BTCUSDT');
      expect(bot.category, TradingBotCategory.linear);
      expect(bot.timeframe, TradingBotTimeframe.fiveMinutes);
      expect(bot.status, TradingBotStatus.running);
      expect(bot.status.isActive, isTrue);
      expect(bot.paperTrading, isTrue);
      expect(bot.dryRun, isTrue);
      expect(bot.strategyConfig['period'], 14);
      expect(bot.createdAt.isUtc, isTrue);
      expect(bot.updatedAt.isUtc, isTrue);
    });

    test('parses nullable runtime fields', () {
      final bot = BackendTradingBot.fromJson(<String, dynamic>{
        ..._botJson(status: 'STOPPED'),
        'exchange_account_id': null,
        'description': null,
        'last_error': null,
        'started_at': null,
        'stopped_at': null,
        'last_run_at': null,
      });

      expect(bot.exchangeAccountId, isNull);
      expect(bot.description, isNull);
      expect(bot.lastError, isNull);
      expect(bot.startedAt, isNull);
      expect(bot.stoppedAt, isNull);
      expect(bot.lastRunAt, isNull);
    });

    test('rejects unsupported backend enums', () {
      expect(
        () => BackendTradingBot.fromJson(<String, dynamic>{
          ..._botJson(status: 'UNKNOWN'),
        }),
        throwsFormatException,
      );
    });
  });

  group('TradingBotCreateRequest', () {
    test('normalizes and serializes a safe bot', () {
      const request = TradingBotCreateRequest(
        exchangeAccountId: 3,
        name: '  Momentum   Alpha  ',
        description: '  Paper strategy  ',
        strategyType: TradingBotStrategyType.momentum,
        symbol: ' btcusdt ',
        category: TradingBotCategory.linear,
        timeframe: TradingBotTimeframe.fiveMinutes,
        stopLossPercent: 2,
        takeProfitPercent: 4,
        strategyConfig: <String, dynamic>{'period': 14},
      );

      final json = request.toJson();

      expect(json['exchange_account_id'], 3);
      expect(json['name'], 'Momentum Alpha');
      expect(json['description'], 'Paper strategy');
      expect(json['strategy_type'], 'MOMENTUM');
      expect(json['symbol'], 'BTCUSDT');
      expect(json['category'], 'linear');
      expect(json['timeframe'], '5m');
      expect(json['paper_trading'], isTrue);
      expect(json['dry_run'], isTrue);
      expect(json['strategy_config'], <String, dynamic>{'period': 14});
    });

    test('rejects unsafe execution settings', () {
      const request = TradingBotCreateRequest(
        name: 'Unsafe Bot',
        symbol: 'BTCUSDT',
        paperTrading: false,
        dryRun: false,
      );

      expect(request.toJson, throwsFormatException);
    });

    test('rejects an invalid risk hierarchy', () {
      const request = TradingBotCreateRequest(
        name: 'Risk Bot',
        symbol: 'BTCUSDT',
        riskPerTradePercent: 5,
        maxDailyLossPercent: 3,
        maxDrawdownPercent: 10,
      );

      expect(request.toJson, throwsFormatException);
    });
  });

  group('TradingBotUpdateRequest', () {
    test('serializes only supplied fields', () {
      const request = TradingBotUpdateRequest(
        name: 'Updated Bot',
        timeframe: TradingBotTimeframe.fifteenMinutes,
        dryRun: true,
      );

      expect(request.toJson(), <String, Object?>{
        'name': 'Updated Bot',
        'timeframe': '15m',
        'dry_run': true,
      });
    });

    test('rejects an empty update', () {
      const request = TradingBotUpdateRequest();

      expect(request.toJson, throwsFormatException);
    });
  });

  test('parses lifecycle action results', () {
    final result = TradingBotLifecycleResult.fromJson(<String, dynamic>{
      'action': 'START',
      'previous_status': 'STOPPED',
      'status': 'RUNNING',
      'changed': true,
      'bot': _botJson(status: 'RUNNING'),
    });

    expect(result.action, TradingBotLifecycleAction.start);
    expect(result.previousStatus, TradingBotStatus.stopped);
    expect(result.status, TradingBotStatus.running);
    expect(result.changed, isTrue);
    expect(result.bot.status, TradingBotStatus.running);
  });
}

Map<String, dynamic> _botJson({required String status}) {
  return <String, dynamic>{
    'id': 10,
    'user_id': 7,
    'exchange_account_id': 3,
    'name': 'Lifecycle Bot',
    'description': 'Lifecycle API bot',
    'strategy_type': 'MOMENTUM',
    'symbol': 'BTCUSDT',
    'category': 'linear',
    'timeframe': '5m',
    'status': status,
    'paper_trading': true,
    'dry_run': true,
    'risk_per_trade_percent': 1,
    'max_position_value_usd': 25,
    'max_daily_loss_percent': 3,
    'max_drawdown_percent': 10,
    'stop_loss_percent': 2,
    'take_profit_percent': 4,
    'strategy_config': <String, dynamic>{'period': 14},
    'last_error': null,
    'started_at': null,
    'stopped_at': null,
    'last_run_at': null,
    'created_at': '2026-07-21T13:00:00Z',
    'updated_at': '2026-07-21T13:00:00Z',
  };
}
