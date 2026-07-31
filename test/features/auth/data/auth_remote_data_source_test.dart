import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/core/network/backend_dio_client.dart';
import 'package:p_trader_ai/features/auth/data/auth_remote_data_source.dart';

void main() {
  group('DioAuthRemoteDataSource', () {
    test('sends login JSON and parses the access token', () async {
      final adapter = _AuthHttpClientAdapter(
        statusCode: 200,
        responseBody: const <String, dynamic>{
          'access_token': 'access-token',
          'token_type': 'bearer',
        },
      );

      final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
        ..httpClientAdapter = adapter;

      final dataSource = DioAuthRemoteDataSource(
        BackendDioClient(tokenStorage: _EmptyTokenStorage(), dio: dio),
      );

      final token = await dataSource.login(
        email: 'user@example.com',
        password: 'Password123',
      );

      expect(adapter.lastPath, '/api/v1/auth/login');
      expect(adapter.lastData, const <String, String>{
        'email': 'user@example.com',
        'password': 'Password123',
      });
      expect(token.accessToken, 'access-token');
    });

    test('uses the backend detail for failed login', () async {
      final adapter = _AuthHttpClientAdapter(
        statusCode: 401,
        responseBody: const <String, dynamic>{
          'detail': 'Incorrect email or password',
        },
      );

      final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
        ..httpClientAdapter = adapter;

      final dataSource = DioAuthRemoteDataSource(
        BackendDioClient(tokenStorage: _EmptyTokenStorage(), dio: dio),
      );

      await expectLater(
        dataSource.login(email: 'user@example.com', password: 'WrongPassword'),
        throwsA(
          isA<AppException>().having(
            (error) => error.message,
            'message',
            'Incorrect email or password',
          ),
        ),
      );
    });
  });
}

class _EmptyTokenStorage implements TokenStorage {
  @override
  Future<void> deleteAccessToken() async {}

  @override
  Future<String?> readAccessToken() async => null;

  @override
  Future<void> writeAccessToken(String token, {bool persist = true}) async {}
}

class _AuthHttpClientAdapter implements HttpClientAdapter {
  _AuthHttpClientAdapter({
    required this.statusCode,
    required this.responseBody,
  });

  final int statusCode;
  final Map<String, dynamic> responseBody;

  String? lastPath;
  Object? lastData;

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
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
