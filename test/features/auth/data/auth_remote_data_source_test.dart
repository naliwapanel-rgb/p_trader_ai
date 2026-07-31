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

      final dataSource = _buildDataSource(adapter);

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

    test('uses the backend message for failed login', () async {
      final adapter = _AuthHttpClientAdapter(
        statusCode: 401,
        responseBody: const <String, dynamic>{
          'success': false,
          'message': 'Incorrect email or password',
          'data': null,
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);

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

    test('parses the authenticated user envelope', () async {
      final adapter = _AuthHttpClientAdapter(
        statusCode: 200,
        responseBody: const <String, dynamic>{
          'success': true,
          'message': 'User profile retrieved successfully',
          'data': <String, dynamic>{
            'id': 7,
            'full_name': 'Test User',
            'email': 'user@example.com',
            'is_active': true,
            'created_at': '2026-07-31T10:30:00Z',
          },
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);
      final user = await dataSource.getCurrentUser();

      expect(adapter.lastPath, '/api/v1/users/me');
      expect(user.id, 7);
      expect(user.fullName, 'Test User');
    });

    test('preserves invalid-token status and message', () async {
      final adapter = _AuthHttpClientAdapter(
        statusCode: 401,
        responseBody: const <String, dynamic>{
          'success': false,
          'message': 'Invalid or expired token',
          'data': null,
          'errors': null,
        },
      );

      final dataSource = _buildDataSource(adapter);

      await expectLater(
        dataSource.getCurrentUser(),
        throwsA(
          isA<AppException>()
              .having((error) => error.statusCode, 'statusCode', 401)
              .having(
                (error) => error.message,
                'message',
                'Invalid or expired token',
              ),
        ),
      );
    });
  });
}

DioAuthRemoteDataSource _buildDataSource(HttpClientAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'))
    ..httpClientAdapter = adapter;

  return DioAuthRemoteDataSource(
    BackendDioClient(tokenStorage: _EmptyTokenStorage(), dio: dio),
  );
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
