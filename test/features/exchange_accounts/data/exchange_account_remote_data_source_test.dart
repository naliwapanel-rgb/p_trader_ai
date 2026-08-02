import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/core/network/backend_dio_client.dart';
import 'package:p_trader_ai/features/exchange_accounts/data/exchange_account_remote_data_source.dart';

void main() {
  group('DioExchangeAccountRemoteDataSource', () {
    test('lists exchange accounts', () async {
      final adapter = _RecordingAdapter(
        responseData: _envelope(<Map<String, Object?>>[_accountJson()]),
      );

      final remote = _remote(adapter);
      final accounts = await remote.listAccounts();

      expect(adapter.lastRequest?.method, 'GET');
      expect(adapter.lastRequest?.uri.path, '/api/v1/exchange-accounts');
      expect(accounts, hasLength(1));
      expect(accounts.single.exchangeName, 'BYBIT');
    });

    test('creates an exchange account', () async {
      final adapter = _RecordingAdapter(
        responseData: _envelope(_accountJson()),
      );

      final remote = _remote(adapter);

      await remote.createAccount(
        exchangeName: ' bybit ',
        accountName: ' Main Account ',
        apiKey: ' api-key-value ',
        apiSecret: ' secret-value ',
        isTestnet: false,
      );

      expect(adapter.lastRequest?.method, 'POST');
      expect(adapter.lastRequest?.uri.path, '/api/v1/exchange-accounts');
      expect(adapter.lastRequest?.data, <String, Object>{
        'exchange_name': 'BYBIT',
        'account_name': 'Main Account',
        'api_key': 'api-key-value',
        'api_secret': 'secret-value',
        'is_testnet': false,
      });
    });

    test('updates only supplied account fields', () async {
      final adapter = _RecordingAdapter(
        responseData: _envelope(_accountJson(accountName: 'Updated Account')),
      );

      final remote = _remote(adapter);

      await remote.updateAccount(
        accountId: 4,
        accountName: ' Updated Account ',
        isActive: false,
      );

      expect(adapter.lastRequest?.method, 'PUT');
      expect(adapter.lastRequest?.uri.path, '/api/v1/exchange-accounts/4');
      expect(adapter.lastRequest?.data, <String, Object>{
        'account_name': 'Updated Account',
        'is_active': false,
      });
    });

    test('deletes an exchange account', () async {
      final adapter = _RecordingAdapter(responseData: _envelope(null));

      await _remote(adapter).deleteAccount(9);

      expect(adapter.lastRequest?.method, 'DELETE');
      expect(adapter.lastRequest?.uri.path, '/api/v1/exchange-accounts/9');
    });

    test('tests an exchange connection', () async {
      final adapter = _RecordingAdapter(
        responseData: _envelope(<String, Object?>{
          'connected': true,
          'account_type': 'UNIFIED',
        }),
      );

      final result = await _remote(adapter).testConnection(3);

      expect(
        adapter.lastRequest?.uri.path,
        '/api/v1/exchange-connections/3/test',
      );
      expect(result.appearsConnected, isTrue);
      expect(result.summary, 'UNIFIED');
    });

    test('parses normalized exchange balance', () async {
      final adapter = _RecordingAdapter(
        responseData: _envelope(<String, Object?>{
          'account_type': 'UNIFIED',
          'total_equity_usd': 1250.5,
          'total_wallet_balance_usd': 1200.25,
          'total_available_balance_usd': 950,
          'total_unrealized_pnl_usd': 50.25,
          'coins': <Map<String, Object?>>[
            <String, Object?>{
              'coin': 'USDT',
              'wallet_balance': 950,
              'available_balance': 900,
              'locked_balance': 50,
            },
          ],
        }),
      );

      final balance = await _remote(adapter).getBalance(3);

      expect(adapter.lastRequest?.method, 'GET');
      expect(
        adapter.lastRequest?.uri.path,
        '/api/v1/exchange-connections/3/balance',
      );
      expect(balance.totalEquityUsd, 1250.5);
      expect(balance.coins.single.symbol, 'USDT');
    });

    test('preserves backend error message', () async {
      final adapter = _RecordingAdapter(
        statusCode: 400,
        responseData: <String, Object?>{'detail': 'Unsupported exchange'},
      );

      await expectLater(
        _remote(adapter).createAccount(
          exchangeName: 'UNKNOWN',
          accountName: 'Test',
          apiKey: 'key-value',
          apiSecret: 'secret-value',
          isTestnet: false,
        ),
        throwsA(
          isA<AppException>()
              .having((error) => error.statusCode, 'statusCode', 400)
              .having(
                (error) => error.message,
                'message',
                'Unsupported exchange',
              ),
        ),
      );
    });
  });
}

DioExchangeAccountRemoteDataSource _remote(_RecordingAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'));

  dio.httpClientAdapter = adapter;

  return DioExchangeAccountRemoteDataSource(
    BackendDioClient(tokenStorage: _MemoryTokenStorage('test-token'), dio: dio),
  );
}

Map<String, Object?> _envelope(Object? data) {
  return <String, Object?>{
    'success': true,
    'message': 'Operation successful',
    'data': data,
    'errors': null,
  };
}

Map<String, Object?> _accountJson({String accountName = 'Main Account'}) {
  return <String, Object?>{
    'id': 4,
    'user_id': 7,
    'exchange_name': 'BYBIT',
    'account_name': accountName,
    'is_testnet': false,
    'is_active': true,
    'created_at': '2026-08-01T10:00:00+00:00',
  };
}

class _MemoryTokenStorage implements TokenStorage {
  _MemoryTokenStorage(this.token);

  String? token;

  @override
  Future<void> deleteAccessToken() async {
    token = null;
  }

  @override
  Future<String?> readAccessToken() async {
    return token;
  }

  @override
  Future<void> writeAccessToken(String token, {required bool persist}) async {
    this.token = token;
  }
}

class _RecordingAdapter implements HttpClientAdapter {
  _RecordingAdapter({required this.responseData, this.statusCode = 200});

  final Object? responseData;
  final int statusCode;

  RequestOptions? lastRequest;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastRequest = options;

    return ResponseBody.fromString(
      jsonEncode(responseData),
      statusCode,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>[Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
