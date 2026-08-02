import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/network/backend_dio_client.dart';

void main() {
  group('BackendDioClient runtime 401 handling', () {
    test('clears the active token and emits expiry '
        'for protected 401 responses', () async {
      final storage = _MemoryTokenStorage('active-token');

      var callbackCalls = 0;
      String? callbackMessage;

      final client = _buildClient(
        storage: storage,
        adapter: _UnauthorizedAdapter(
          responseBody: const <String, Object?>{
            'message': 'Invalid or expired token',
          },
        ),
        onUnauthorized: (message) {
          callbackCalls += 1;
          callbackMessage = message;
        },
      );

      await expectLater(
        client.dio.get<Object?>('/portfolios'),
        throwsA(isA<DioException>()),
      );

      expect(storage.token, isNull);
      expect(storage.deleteCalls, 1);
      expect(callbackCalls, 1);
      expect(callbackMessage, 'Invalid or expired token');
    });

    test('does not expire the session for login 401', () async {
      final storage = _MemoryTokenStorage('existing-token');

      var callbackCalls = 0;

      final client = _buildClient(
        storage: storage,
        adapter: _UnauthorizedAdapter(
          responseBody: const <String, Object?>{
            'message': 'Incorrect email or password',
          },
        ),
        onUnauthorized: (_) {
          callbackCalls += 1;
        },
      );

      await expectLater(
        client.dio.post<Object?>(
          '/auth/login',
          data: const <String, String>{
            'email': 'user@example.com',
            'password': 'wrong',
          },
        ),
        throwsA(isA<DioException>()),
      );

      expect(storage.token, 'existing-token');
      expect(storage.deleteCalls, 0);
      expect(callbackCalls, 0);
    });

    test('does not delete a newer token when an old '
        'request returns 401 late', () async {
      final storage = _MemoryTokenStorage('old-token');

      var callbackCalls = 0;

      final client = _buildClient(
        storage: storage,
        adapter: _UnauthorizedAdapter(
          responseBody: const <String, Object?>{
            'message': 'Invalid or expired token',
          },
          beforeResponse: () {
            storage.token = 'new-token';
          },
        ),
        onUnauthorized: (_) {
          callbackCalls += 1;
        },
      );

      await expectLater(
        client.dio.get<Object?>('/portfolios'),
        throwsA(isA<DioException>()),
      );

      expect(storage.token, 'new-token');
      expect(storage.deleteCalls, 0);
      expect(callbackCalls, 0);
    });

    test('emits expiry only once after token removal', () async {
      final storage = _MemoryTokenStorage('active-token');

      var callbackCalls = 0;

      final client = _buildClient(
        storage: storage,
        adapter: _UnauthorizedAdapter(
          responseBody: const <String, Object?>{
            'message': 'Invalid or expired token',
          },
        ),
        onUnauthorized: (_) {
          callbackCalls += 1;
        },
      );

      await expectLater(
        client.dio.get<Object?>('/portfolios'),
        throwsA(isA<DioException>()),
      );

      await expectLater(
        client.dio.get<Object?>('/exchange-accounts'),
        throwsA(isA<DioException>()),
      );

      expect(storage.deleteCalls, 1);
      expect(callbackCalls, 1);
    });
  });
}

BackendDioClient _buildClient({
  required _MemoryTokenStorage storage,
  required HttpClientAdapter adapter,
  required UnauthorizedCallback onUnauthorized,
}) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
    ..httpClientAdapter = adapter;

  return BackendDioClient(
    tokenStorage: storage,
    onUnauthorized: onUnauthorized,
    dio: dio,
  );
}

class _MemoryTokenStorage implements TokenStorage {
  _MemoryTokenStorage(this.token);

  String? token;
  int deleteCalls = 0;

  @override
  Future<void> deleteAccessToken() async {
    deleteCalls += 1;
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

class _UnauthorizedAdapter implements HttpClientAdapter {
  _UnauthorizedAdapter({required this.responseBody, this.beforeResponse});

  final Map<String, Object?> responseBody;
  final void Function()? beforeResponse;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    beforeResponse?.call();

    return ResponseBody.fromString(
      jsonEncode(responseBody),
      401,
      headers: <String, List<String>>{
        Headers.contentTypeHeader: <String>[Headers.jsonContentType],
      },
    );
  }

  @override
  void close({bool force = false}) {}
}
