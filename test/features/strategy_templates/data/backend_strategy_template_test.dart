import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';

void main() {
  test('parses a backend strategy template', () {
    final template = BackendStrategyTemplate.fromJson(_templateJson());

    expect(template.id, 10);
    expect(template.userId, 7);
    expect(template.name, 'Momentum Template');
    expect(template.strategyType, TradingBotStrategyType.momentum);
    expect(template.symbol, 'BTCUSDT');
    expect(template.visibility, StrategyTemplateVisibility.privateTemplate);
    expect(template.status, StrategyTemplateStatus.draft);
    expect(template.version, 1);
    expect(template.paperTrading, isTrue);
    expect(template.dryRun, isTrue);
  });

  test('serializes and normalizes a safe template', () {
    final payload = const StrategyTemplateCreateRequest(
      name: '  Momentum   Template ',
      symbol: ' btcusdt ',
      strategyType: TradingBotStrategyType.momentum,
    ).toJson();

    expect(payload['name'], 'Momentum Template');
    expect(payload['symbol'], 'BTCUSDT');
    expect(payload['strategy_type'], 'MOMENTUM');
    expect(payload['visibility'], 'PRIVATE');
    expect(payload['paper_trading'], isTrue);
    expect(payload['dry_run'], isTrue);
  });

  test('rejects unsafe template execution settings', () {
    expect(
      () => const StrategyTemplateCreateRequest(
        name: 'Unsafe Template',
        symbol: 'BTCUSDT',
        paperTrading: false,
        dryRun: false,
      ).toJson(),
      throwsA(isA<FormatException>()),
    );
  });

  test('requires at least one update field', () {
    expect(
      () => const StrategyTemplateUpdateRequest().toJson(),
      throwsA(isA<FormatException>()),
    );
  });

  test('serializes safe bot creation from template', () {
    final payload = const StrategyTemplateBotCreateRequest(
      exchangeAccountId: 4,
      name: '  Copied   Bot ',
      description: ' follower bot ',
    ).toJson();

    expect(payload, <String, Object?>{
      'exchange_account_id': 4,
      'name': 'Copied Bot',
      'description': 'follower bot',
    });
  });

  test('parses a strategy-template action result', () {
    final result = StrategyTemplateActionResult.fromJson(<String, dynamic>{
      'action': 'PUBLISH',
      'previous_status': 'DRAFT',
      'status': 'PUBLISHED',
      'changed': true,
      'template': _templateJson(
        status: 'PUBLISHED',
        visibility: 'PUBLIC',
        publishedAt: '2026-08-04T08:00:00Z',
      ),
    });

    expect(result.action, StrategyTemplateAction.publish);
    expect(result.previousStatus, StrategyTemplateStatus.draft);
    expect(result.status, StrategyTemplateStatus.published);
    expect(result.changed, isTrue);
    expect(
      result.template.visibility,
      StrategyTemplateVisibility.publicTemplate,
    );
  });
}

Map<String, dynamic> _templateJson({
  String status = 'DRAFT',
  String visibility = 'PRIVATE',
  String? publishedAt,
}) {
  return <String, dynamic>{
    'id': 10,
    'user_id': 7,
    'name': 'Momentum Template',
    'description': 'Safe strategy template',
    'strategy_type': 'MOMENTUM',
    'symbol': 'BTCUSDT',
    'category': 'linear',
    'timeframe': '5m',
    'visibility': visibility,
    'paper_trading': true,
    'dry_run': true,
    'risk_per_trade_percent': 1,
    'max_position_value_usd': 25,
    'max_daily_loss_percent': 3,
    'max_drawdown_percent': 10,
    'stop_loss_percent': 2,
    'take_profit_percent': 4,
    'strategy_config': <String, dynamic>{'period': 14},
    'status': status,
    'version': 1,
    'published_at': publishedAt,
    'archived_at': null,
    'created_at': '2026-08-04T07:00:00Z',
    'updated_at': '2026-08-04T07:00:00Z',
  };
}
