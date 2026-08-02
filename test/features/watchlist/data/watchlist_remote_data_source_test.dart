import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/core/network/backend_dio_client.dart';
import 'package:p_trader_ai/features/watchlist/data/watchlist_remote_data_source.dart';

void main() {
  group('DioWatchlistRemoteDataSource', () {
    test('lists backend watchlist items', () async {
      final adapter = _WatchlistAdapter(
        statusCode: 200,
        responseBody: const <String, Object?>{
          'success': true,
          'message': 'Watchlist items retrieved successfully',
          'data': <Object?>[
            <String, Object?>{
              'id': 4,
              'user_id': 7,
              'symbol': 'BTCUSDT',
              'exchange': 'BYBIT',
              'created_at': '2026-08-02T20:00:00Z',
            },
          ],
        },
      );

      final source = _buildSource(adapter);
      final items = await source.listItems();

      expect(adapter.lastMethod, 'GET');
      expect(adapter.lastPath, '/api/v1/watchlists');
      expect(items, hasLength(1));
      expect(items.single.symbol, 'BTCUSDT');
    });

    test('creates a normalized Bybit watchlist item', () async {
      final adapter = _WatchlistAdapter(
        statusCode: 200,
        responseBody: const <String, Object?>{
          'success': true,
          'message': 'Watchlist item created successfully',
          'data': <String, Object?>{
            'id': 5,
            'user_id': 7,
            'symbol': 'ETHUSDT',
            'exchange': 'BYBIT',
            'created_at': '2026-08-02T20:01:00Z',
          },
        },
      );

      final source = _buildSource(adapter);

      final item = await source.createItem(symbol: 'eth', exchange: 'bybit');

      expect(adapter.lastMethod, 'POST');
      expect(adapter.lastPath, '/api/v1/watchlists');
      expect(adapter.lastData, const <String, Object>{
        'symbol': 'ETHUSDT',
        'exchange': 'BYBIT',
      });
      expect(item.symbol, 'ETHUSDT');
    });

    test('deletes by backend item ID', () async {
      final adapter = _WatchlistAdapter(
        statusCode: 200,
        responseBody: const <String, Object?>{
          'success': true,
          'message': 'Watchlist item deleted successfully',
          'data': null,
        },
      );

      final source = _buildSource(adapter);

      await source.deleteItem(9);

      expect(adapter.lastMethod, 'DELETE');
      expect(adapter.lastPath, '/api/v1/watchlists/9');
    });

    test('preserves duplicate conflict details', () async {
      final adapter = _WatchlistAdapter(
        statusCode: 409,
        responseBody: const <String, Object?>{
          'detail': 'Symbol already exists in watchlist',
        },
      );

      final source = _buildSource(adapter);

      await expectLater(
        source.createItem(symbol: 'btc', exchange: 'BYBIT'),
        throwsA(
          isA<AppException>()
              .having((error) => error.statusCode, 'statusCode', 409)
              .having(
                (error) => error.message,
                'message',
                'Symbol already exists in watchlist',
              ),
        ),
      );
    });
  });
}

DioWatchlistRemoteDataSource _buildSource(HttpClientAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
    ..httpClientAdapter = adapter;

  return DioWatchlistRemoteDataSource(
    BackendDioClient(tokenStorage: _EmptyTokenStorage(), dio: dio),
  );
}

class _EmptyTokenStorage implements TokenStorage {
  @override
  Future<void> deleteAccessToken() async {}

  @override
  Future<String?> readAccessToken() async {
    return null;
  }

  @override
  Future<void> writeAccessToken(String token, {bool persist = true}) async {}
}

class _WatchlistAdapter implements HttpClientAdapter {
  _WatchlistAdapter({required this.statusCode, required this.responseBody});

  final int statusCode;
  final Map<String, Object?> responseBody;

  String? lastMethod;
  String? lastPath;
  Object? lastData;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastMethod = options.method;
    lastPath = options.uri.path;
    lastData = options.data;

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
