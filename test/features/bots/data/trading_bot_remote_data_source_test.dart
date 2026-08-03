import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/bots/data/backend_trading_bot.dart';
import 'package:p_trader_ai/features/bots/data/trading_bot_remote_data_source.dart';

void main() {
  late Dio dio;
  late DioAdapter adapter;
  late DioTradingBotRemoteDataSource dataSource;

  setUp(() {
    dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'));
    adapter = DioAdapter(dio: dio);
    dataSource = DioTradingBotRemoteDataSource(dio);
  });

  test('lists trading bots with filters', () async {
    adapter.onGet(
      '/trading-bots',
      (server) => server.reply(200, <String, dynamic>{
        'success': true,
        'data': <Map<String, dynamic>>[_botJson(status: 'RUNNING')],
      }),
      queryParameters: <String, dynamic>{
        'status': 'RUNNING',
        'limit': 25,
        'offset': 5,
      },
    );

    final result = await dataSource.listBots(
      status: TradingBotStatus.running,
      limit: 25,
      offset: 5,
    );

    expect(result, hasLength(1));
    expect(result.single.id, 10);
    expect(result.single.status, TradingBotStatus.running);
  });

  test('creates a trading bot', () async {
    adapter.onPost(
      '/trading-bots',
      (server) => server.reply(200, <String, dynamic>{
        'success': true,
        'data': _botJson(status: 'DRAFT'),
      }),
      data: <String, Object?>{
        'name': 'Momentum Bot',
        'strategy_type': 'MOMENTUM',
        'symbol': 'BTCUSDT',
        'category': 'linear',
        'timeframe': '5m',
        'paper_trading': true,
        'dry_run': true,
        'risk_per_trade_percent': 1.0,
        'max_position_value_usd': 25.0,
        'max_daily_loss_percent': 3.0,
        'max_drawdown_percent': 10.0,
        'strategy_config': <String, dynamic>{'period': 14},
      },
    );

    final result = await dataSource.createBot(
      const TradingBotCreateRequest(
        name: 'Momentum Bot',
        strategyType: TradingBotStrategyType.momentum,
        symbol: 'BTCUSDT',
        strategyConfig: <String, dynamic>{'period': 14},
      ),
    );

    expect(result.status, TradingBotStatus.draft);
  });

  test('updates only supplied trading-bot fields', () async {
    adapter.onPut(
      '/trading-bots/10',
      (server) => server.reply(200, <String, dynamic>{
        'success': true,
        'data': <String, dynamic>{
          ..._botJson(status: 'STOPPED'),
          'name': 'Updated Bot',
          'timeframe': '15m',
        },
      }),
      data: <String, Object?>{'name': 'Updated Bot', 'timeframe': '15m'},
    );

    final result = await dataSource.updateBot(
      botId: 10,
      request: const TradingBotUpdateRequest(
        name: 'Updated Bot',
        timeframe: TradingBotTimeframe.fifteenMinutes,
      ),
    );

    expect(result.name, 'Updated Bot');
    expect(result.timeframe, TradingBotTimeframe.fifteenMinutes);
  });

  for (final action in TradingBotLifecycleAction.values) {
    test('posts ${action.name} lifecycle action', () async {
      final status = switch (action) {
        TradingBotLifecycleAction.prepare => 'STOPPED',
        TradingBotLifecycleAction.start => 'RUNNING',
        TradingBotLifecycleAction.pause => 'PAUSED',
        TradingBotLifecycleAction.resume => 'RUNNING',
        TradingBotLifecycleAction.stop => 'STOPPED',
      };

      adapter.onPost(
        '/trading-bots/10/${action.routeValue}',
        (server) => server.reply(200, <String, dynamic>{
          'success': true,
          'data': <String, dynamic>{
            'action': action.backendValue,
            'previous_status': 'STOPPED',
            'status': status,
            'changed': true,
            'bot': _botJson(status: status),
          },
        }),
      );

      final result = await dataSource.performLifecycle(
        botId: 10,
        action: action,
      );

      expect(result.action, action);
      expect(result.bot.id, 10);
      expect(result.status.backendValue, status);
    });
  }

  test('deletes a stopped trading bot', () async {
    adapter.onDelete(
      '/trading-bots/10',
      (server) => server.reply(200, <String, dynamic>{
        'success': true,
        'message': 'Trading bot deleted successfully',
      }),
    );

    await expectLater(dataSource.deleteBot(10), completes);
  });

  test('preserves backend status and message', () async {
    adapter.onPost(
      '/trading-bots/10/start',
      (server) => server.reply(409, <String, dynamic>{
        'success': false,
        'message': 'Trading bot execution safety validation failed',
      }),
    );

    try {
      await dataSource.performLifecycle(
        botId: 10,
        action: TradingBotLifecycleAction.start,
      );
      fail('Expected AppException');
    } on AppException catch (error) {
      expect(error.statusCode, 409);
      expect(error.message, 'Trading bot execution safety validation failed');
    }
  });
}

Map<String, dynamic> _botJson({required String status}) {
  return <String, dynamic>{
    'id': 10,
    'user_id': 7,
    'exchange_account_id': 3,
    'name': 'Momentum Bot',
    'description': 'Backend bot',
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

class DioAdapter implements HttpClientAdapter {
  DioAdapter({required Dio dio}) {
    dio.httpClientAdapter = this;
  }

  final List<_MockRoute> _routes = <_MockRoute>[];

  void onGet(
    String path,
    void Function(MockServer server) handler, {
    Map<String, dynamic>? queryParameters,
    Object? data,
  }) {
    _register(
      method: 'GET',
      path: path,
      handler: handler,
      queryParameters: queryParameters,
      data: data,
    );
  }

  void onPost(
    String path,
    void Function(MockServer server) handler, {
    Map<String, dynamic>? queryParameters,
    Object? data,
  }) {
    _register(
      method: 'POST',
      path: path,
      handler: handler,
      queryParameters: queryParameters,
      data: data,
    );
  }

  void onPut(
    String path,
    void Function(MockServer server) handler, {
    Map<String, dynamic>? queryParameters,
    Object? data,
  }) {
    _register(
      method: 'PUT',
      path: path,
      handler: handler,
      queryParameters: queryParameters,
      data: data,
    );
  }

  void onDelete(
    String path,
    void Function(MockServer server) handler, {
    Map<String, dynamic>? queryParameters,
    Object? data,
  }) {
    _register(
      method: 'DELETE',
      path: path,
      handler: handler,
      queryParameters: queryParameters,
      data: data,
    );
  }

  void _register({
    required String method,
    required String path,
    required void Function(MockServer server) handler,
    required Map<String, dynamic>? queryParameters,
    required Object? data,
  }) {
    final server = MockServer();
    handler(server);

    if (!server.hasReply) {
      throw StateError('The mocked route did not configure a reply.');
    }

    _routes.add(
      _MockRoute(
        method: method,
        path: path,
        queryParameters: queryParameters,
        expectedData: data,
        statusCode: server.statusCode!,
        responseBody: server.responseBody,
      ),
    );
  }

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    for (final route in _routes) {
      if (!route.matches(options)) {
        continue;
      }

      return ResponseBody.fromString(
        jsonEncode(route.responseBody),
        route.statusCode,
        headers: <String, List<String>>{
          Headers.contentTypeHeader: <String>[Headers.jsonContentType],
        },
      );
    }

    throw StateError(
      'No mock matched '
      '${options.method} ${options.uri}. '
      'Request data: ${options.data}',
    );
  }

  @override
  void close({bool force = false}) {}
}

class MockServer {
  int? statusCode;
  Object? responseBody;

  bool get hasReply => statusCode != null;

  void reply(int statusCode, Object? responseBody) {
    this.statusCode = statusCode;
    this.responseBody = responseBody;
  }
}

class _MockRoute {
  const _MockRoute({
    required this.method,
    required this.path,
    required this.queryParameters,
    required this.expectedData,
    required this.statusCode,
    required this.responseBody,
  });

  final String method;
  final String path;
  final Map<String, dynamic>? queryParameters;
  final Object? expectedData;
  final int statusCode;
  final Object? responseBody;

  bool matches(RequestOptions options) {
    if (options.method.toUpperCase() != method) {
      return false;
    }

    final pathMatches = options.path == path || options.uri.path.endsWith(path);

    if (!pathMatches) {
      return false;
    }

    if (queryParameters != null &&
        !_jsonEquals(options.queryParameters, queryParameters)) {
      return false;
    }

    if (expectedData != null && !_jsonEquals(options.data, expectedData)) {
      return false;
    }

    return true;
  }
}

bool _jsonEquals(Object? first, Object? second) {
  return jsonEncode(first) == jsonEncode(second);
}
