import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/core/network/backend_dio_client.dart';
import 'package:p_trader_ai/features/portfolio/data/live_portfolio_remote_data_source.dart';

void main() {
  group('DioLivePortfolioRemoteDataSource', () {
    test('lists backend portfolios', () async {
      final adapter = _PortfolioAdapter(
        responseBody: <String, dynamic>{
          'success': true,
          'message': 'Portfolios retrieved successfully',
          'data': <Map<String, dynamic>>[_portfolioJson()],
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);
      final portfolios = await dataSource.listPortfolios();

      expect(adapter.lastMethod, 'GET');
      expect(adapter.lastPath, '/api/v1/portfolios');
      expect(portfolios, hasLength(1));
      expect(portfolios.single.name, 'Live Portfolio');
      expect(portfolios.single.totalValue, 1250);
    });

    test('creates a backend portfolio', () async {
      final adapter = _PortfolioAdapter(
        responseBody: <String, dynamic>{
          'success': true,
          'message': 'Portfolio created successfully',
          'data': _portfolioJson(),
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);

      final portfolio = await dataSource.createPortfolio(
        name: ' Live Portfolio ',
        baseCurrency: 'usdt',
      );

      expect(adapter.lastMethod, 'POST');
      expect(adapter.lastPath, '/api/v1/portfolios');
      expect(adapter.lastData, <String, Object>{
        'name': 'Live Portfolio',
        'base_currency': 'USDT',
      });
      expect(portfolio.id, 4);
    });

    test('synchronizes a backend portfolio', () async {
      final adapter = _PortfolioAdapter(
        responseBody: <String, dynamic>{
          'success': true,
          'message': 'Portfolio synchronization completed successfully',
          'data': <String, dynamic>{
            'snapshot': _snapshotJson(),
            'created': true,
            'portfolio_total_value': 1250.0,
            'portfolio_profit_loss': 25.5,
            'source_errors': <String, String>{},
          },
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);

      final result = await dataSource.synchronize(
        portfolioId: 4,
        exchangeAccountId: 1,
        category: 'LINEAR',
        settleCoin: 'usdt',
      );

      expect(adapter.lastMethod, 'POST');
      expect(adapter.lastPath, '/api/v1/portfolios/4/sync');
      expect(adapter.lastData, <String, Object>{
        'exchange_account_id': 1,
        'category': 'linear',
        'settle_coin': 'USDT',
      });
      expect(result.snapshot.status, 'SUCCESS');
      expect(result.snapshot.coins.single.coin, 'BTC');
      expect(result.portfolioTotalValue, 1250);
    });

    test('loads the latest synchronization snapshot', () async {
      final adapter = _PortfolioAdapter(
        responseBody: <String, dynamic>{
          'success': true,
          'message':
              'Latest portfolio synchronization snapshot retrieved successfully',
          'data': _snapshotJson(),
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);

      final snapshot = await dataSource.getLatestSnapshot(
        portfolioId: 4,
        exchangeAccountId: 1,
      );

      expect(adapter.lastPath, '/api/v1/portfolios/4/sync/latest');
      expect(adapter.lastQueryParameters, <String, dynamic>{
        'exchange_account_id': 1,
      });
      expect(snapshot.exchangeName, 'BYBIT');
      expect(snapshot.totalAvailableBalanceUsd, 900);
    });

    test('loads synchronization history', () async {
      final adapter = _PortfolioAdapter(
        responseBody: <String, dynamic>{
          'success': true,
          'message': 'Portfolio synchronization history retrieved successfully',
          'data': <Map<String, dynamic>>[_snapshotJson()],
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);

      final history = await dataSource.listSyncHistory(
        portfolioId: 4,
        limit: 25,
      );

      expect(adapter.lastPath, '/api/v1/portfolios/4/sync/history');
      expect(adapter.lastQueryParameters, <String, dynamic>{'limit': 25});
      expect(history, hasLength(1));
    });

    test('preserves backend error status and message', () async {
      final adapter = _PortfolioAdapter(
        statusCode: 404,
        responseBody: const <String, dynamic>{
          'detail': 'Portfolio synchronization snapshot not found',
        },
      );

      final dataSource = _buildDataSource(adapter);

      await expectLater(
        dataSource.getLatestSnapshot(portfolioId: 4),
        throwsA(
          isA<AppException>()
              .having((error) => error.statusCode, 'statusCode', 404)
              .having(
                (error) => error.message,
                'message',
                'Portfolio synchronization snapshot not found',
              ),
        ),
      );
    });
  });
}

DioLivePortfolioRemoteDataSource _buildDataSource(HttpClientAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
    ..httpClientAdapter = adapter;

  return DioLivePortfolioRemoteDataSource(
    BackendDioClient(tokenStorage: _EmptyTokenStorage(), dio: dio),
  );
}

Map<String, dynamic> _portfolioJson() {
  return <String, dynamic>{
    'id': 4,
    'user_id': 1,
    'name': 'Live Portfolio',
    'base_currency': 'USDT',
    'total_value': 1250.0,
    'profit_loss': 25.5,
    'created_at': '2026-08-02T12:00:00Z',
  };
}

Map<String, dynamic> _snapshotJson() {
  return <String, dynamic>{
    'user_id': 1,
    'portfolio_id': 4,
    'exchange_account_id': 1,
    'exchange_name': 'BYBIT',
    'account_type': 'UNIFIED',
    'category': 'linear',
    'settle_coin': 'USDT',
    'status': 'SUCCESS',
    'fingerprint':
        'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'sync_version': 1,
    'total_equity_usd': 1250.0,
    'total_wallet_balance_usd': 1200.0,
    'total_available_balance_usd': 900.0,
    'total_unrealized_pnl_usd': 25.5,
    'total_realized_pnl_usd': 10.0,
    'total_position_value_usd': 500.0,
    'coin_count': 1,
    'open_position_count': 1,
    'open_order_count': 2,
    'balance_payload': <String, dynamic>{
      'exchange': 'BYBIT',
      'account_type': 'UNIFIED',
      'coins': <Map<String, dynamic>>[
        <String, dynamic>{
          'coin': 'BTC',
          'equity': 0.02,
          'wallet_balance': 0.02,
          'available_balance': 0.01,
          'locked_balance': 0.01,
          'usd_value': 1250.0,
          'unrealized_pnl': 25.5,
        },
      ],
    },
    'positions_payload': <Map<String, dynamic>>[
      <String, dynamic>{'symbol': 'BTCUSDT', 'side': 'Buy'},
    ],
    'orders_payload': <Map<String, dynamic>>[
      <String, dynamic>{'symbol': 'BTCUSDT', 'side': 'Buy'},
    ],
    'error_message': null,
    'id': 10,
    'synced_at': '2026-08-02T12:05:00Z',
    'created_at': '2026-08-02T12:05:00Z',
  };
}

class _EmptyTokenStorage implements TokenStorage {
  @override
  Future<void> deleteAccessToken() async {}

  @override
  Future<String?> readAccessToken() async => null;

  @override
  Future<void> writeAccessToken(String token, {bool persist = true}) async {}
}

class _PortfolioAdapter implements HttpClientAdapter {
  _PortfolioAdapter({required this.responseBody, this.statusCode = 200});

  final Map<String, dynamic> responseBody;
  final int statusCode;

  String? lastMethod;
  String? lastPath;
  Object? lastData;
  Map<String, dynamic>? lastQueryParameters;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastMethod = options.method;
    lastPath = options.uri.path;
    lastData = options.data;
    lastQueryParameters = Map<String, dynamic>.from(options.queryParameters);

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
