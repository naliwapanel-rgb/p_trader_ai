import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/strategy_templates/data/backend_strategy_template.dart';
import 'package:p_trader_ai/features/strategy_templates/data/strategy_template_remote_data_source.dart';

void main() {
  test('lists owned templates with filters', () async {
    final adapter = _SingleResponseAdapter(
      statusCode: 200,
      responseBody: <String, dynamic>{
        'success': true,
        'data': <Map<String, dynamic>>[_templateJson()],
      },
    );

    final templates = await _remote(adapter).listOwned(
      status: StrategyTemplateStatus.draft,
      visibility: StrategyTemplateVisibility.privateTemplate,
      limit: 20,
      offset: 5,
    );

    expect(templates, hasLength(1));
    expect(templates.single.id, 10);

    final request = adapter.lastRequest!;

    expect(request.method, 'GET');
    expect(request.uri.path, '/api/v1/strategy-templates');
    expect(request.queryParameters, <String, dynamic>{
      'status': 'DRAFT',
      'visibility': 'PRIVATE',
      'limit': 20,
      'offset': 5,
    });
  });

  test('creates a strategy template', () async {
    final adapter = _SingleResponseAdapter(
      statusCode: 200,
      responseBody: <String, dynamic>{'success': true, 'data': _templateJson()},
    );

    final template = await _remote(adapter).createTemplate(
      const StrategyTemplateCreateRequest(
        name: 'Momentum Template',
        symbol: 'btcusdt',
        strategyType: TradingBotStrategyType.momentum,
      ),
    );

    expect(template.name, 'Momentum Template');

    final request = adapter.lastRequest!;

    expect(request.method, 'POST');
    expect(request.uri.path, '/api/v1/strategy-templates');

    final payload = Map<String, dynamic>.from(request.data as Map);

    expect(payload['symbol'], 'BTCUSDT');
    expect(payload['strategy_type'], 'MOMENTUM');
    expect(payload['paper_trading'], isTrue);
    expect(payload['dry_run'], isTrue);
  });

  test('updates only supplied template fields', () async {
    final adapter = _SingleResponseAdapter(
      statusCode: 200,
      responseBody: <String, dynamic>{
        'success': true,
        'data': <String, dynamic>{
          ..._templateJson(),
          'name': 'Updated Template',
          'timeframe': '15m',
        },
      },
    );

    final template = await _remote(adapter).updateTemplate(
      templateId: 10,
      request: const StrategyTemplateUpdateRequest(
        name: 'Updated Template',
        timeframe: TradingBotTimeframe.fifteenMinutes,
      ),
    );

    expect(template.name, 'Updated Template');
    expect(template.timeframe, TradingBotTimeframe.fifteenMinutes);

    expect(adapter.lastRequest?.data, <String, Object?>{
      'name': 'Updated Template',
      'timeframe': '15m',
    });
  });

  test('performs a template lifecycle action', () async {
    final adapter = _SingleResponseAdapter(
      statusCode: 200,
      responseBody: <String, dynamic>{
        'success': true,
        'data': <String, dynamic>{
          'action': 'PUBLISH',
          'previous_status': 'DRAFT',
          'status': 'PUBLISHED',
          'changed': true,
          'template': _templateJson(status: 'PUBLISHED', visibility: 'PUBLIC'),
        },
      },
    );

    final result = await _remote(
      adapter,
    ).performAction(templateId: 10, action: StrategyTemplateAction.publish);

    expect(result.status, StrategyTemplateStatus.published);
    expect(
      adapter.lastRequest?.uri.path,
      '/api/v1/strategy-templates/10/publish',
    );
  });

  test('creates a safe bot from a template', () async {
    final adapter = _SingleResponseAdapter(
      statusCode: 200,
      responseBody: <String, dynamic>{'success': true, 'data': _botJson()},
    );

    final bot = await _remote(adapter).createBotFromTemplate(
      templateId: 10,
      request: const StrategyTemplateBotCreateRequest(
        exchangeAccountId: 3,
        name: 'Copied Bot',
      ),
    );

    expect(bot.name, 'Copied Bot');
    expect(bot.paperTrading, isTrue);
    expect(bot.dryRun, isTrue);

    expect(
      adapter.lastRequest?.uri.path,
      '/api/v1/strategy-templates/10/create-bot',
    );

    expect(adapter.lastRequest?.data, <String, Object?>{
      'exchange_account_id': 3,
      'name': 'Copied Bot',
    });
  });

  test('preserves backend status and message', () async {
    final adapter = _SingleResponseAdapter(
      statusCode: 409,
      responseBody: const <String, dynamic>{
        'success': false,
        'message': 'Only draft strategy templates can be published',
        'data': null,
      },
    );

    await expectLater(
      _remote(
        adapter,
      ).performAction(templateId: 10, action: StrategyTemplateAction.publish),
      throwsA(
        isA<AppException>()
            .having((error) => error.statusCode, 'statusCode', 409)
            .having(
              (error) => error.message,
              'message',
              'Only draft strategy templates '
                  'can be published',
            ),
      ),
    );
  });
}

DioStrategyTemplateRemoteDataSource _remote(HttpClientAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'));

  dio.httpClientAdapter = adapter;

  return DioStrategyTemplateRemoteDataSource(dio);
}

Map<String, dynamic> _templateJson({
  String status = 'DRAFT',
  String visibility = 'PRIVATE',
}) {
  return <String, dynamic>{
    'id': 10,
    'user_id': 7,
    'name': 'Momentum Template',
    'description': 'Backend template',
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
    'published_at': null,
    'archived_at': null,
    'created_at': '2026-08-04T07:00:00Z',
    'updated_at': '2026-08-04T07:00:00Z',
  };
}

Map<String, dynamic> _botJson() {
  return <String, dynamic>{
    'id': 20,
    'user_id': 7,
    'exchange_account_id': 3,
    'name': 'Copied Bot',
    'description': null,
    'strategy_type': 'MOMENTUM',
    'symbol': 'BTCUSDT',
    'category': 'linear',
    'timeframe': '5m',
    'status': 'DRAFT',
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
    'created_at': '2026-08-04T07:00:00Z',
    'updated_at': '2026-08-04T07:00:00Z',
  };
}

class _SingleResponseAdapter implements HttpClientAdapter {
  _SingleResponseAdapter({
    required this.statusCode,
    required this.responseBody,
  });

  final int statusCode;
  final Object? responseBody;

  RequestOptions? lastRequest;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastRequest = options;

    return ResponseBody.fromString(
      jsonEncode(responseBody),
      statusCode,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>[Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
