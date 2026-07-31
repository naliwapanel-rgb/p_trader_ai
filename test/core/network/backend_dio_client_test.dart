import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/network/backend_dio_client.dart';

void main() {
  group('BackendDioClient', () {
    test('adds the Bearer token when one is stored', () async {
      final adapter = _CapturingHttpClientAdapter();
      final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
        ..httpClientAdapter = adapter;

      final client = BackendDioClient(
        tokenStorage: _MemoryTokenStorage('test-access-token'),
        dio: dio,
      );

      await client.dio.get<Object?>('/health');

      expect(
        adapter.lastHeaders?[BackendDioClient.authorizationHeader],
        'Bearer test-access-token',
      );
    });

    test('does not add Authorization to authentication requests', () async {
      final adapter = _CapturingHttpClientAdapter();
      final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
        ..httpClientAdapter = adapter;

      final client = BackendDioClient(
        tokenStorage: _MemoryTokenStorage('stale-token'),
        dio: dio,
      );

      await client.dio.post<Object?>(
        '/auth/login',
        data: const <String, String>{
          'email': 'user@example.com',
          'password': 'Password123',
        },
      );

      expect(
        adapter.lastHeaders?.containsKey(BackendDioClient.authorizationHeader),
        isFalse,
      );
    });

    test('does not add Authorization without a token', () async {
      final adapter = _CapturingHttpClientAdapter();
      final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
        ..httpClientAdapter = adapter;

      final client = BackendDioClient(
        tokenStorage: _MemoryTokenStorage(null),
        dio: dio,
      );

      await client.dio.get<Object?>('/health');

      expect(
        adapter.lastHeaders?.containsKey(BackendDioClient.authorizationHeader),
        isFalse,
      );
    });
  });
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
  Future<void> writeAccessToken(String token, {bool persist = true}) async {
    this.token = token;
  }
}

class _CapturingHttpClientAdapter implements HttpClientAdapter {
  Map<String, dynamic>? lastHeaders;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    lastHeaders = Map<String, dynamic>.from(options.headers);

    return ResponseBody.fromString(
      '{"status":"ok"}',
      200,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>[Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
