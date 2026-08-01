import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/core/network/backend_dio_client.dart';
import 'package:p_trader_ai/features/auth/data/auth_remote_data_source.dart';

void main() {
  group('DioAuthRemoteDataSource account management', () {
    test('updates profile and parses returned user', () async {
      final adapter = _RecordingAdapter(
        responseData: _userEnvelope(
          fullName: 'Updated User',
          email: 'updated@example.com',
        ),
      );

      final remote = _remote(adapter);

      final user = await remote.updateProfile(
        fullName: ' Updated User ',
        email: ' UPDATED@EXAMPLE.COM ',
      );

      final request = adapter.lastRequest!;

      expect(request.method, 'PUT');
      expect(request.uri.path, '/api/v1/users/me');
      expect(
        request.headers[BackendDioClient.authorizationHeader],
        'Bearer test-token',
      );
      expect(request.data, <String, String>{
        'full_name': 'Updated User',
        'email': 'updated@example.com',
      });
      expect(user.fullName, 'Updated User');
      expect(user.email, 'updated@example.com');
    });

    test('sends password update contract', () async {
      final adapter = _RecordingAdapter(
        responseData: <String, Object?>{
          'success': true,
          'message': 'Password updated successfully',
        },
      );

      final remote = _remote(adapter);

      await remote.updatePassword(
        currentPassword: 'Password123',
        newPassword: 'NewPassword456',
      );

      final request = adapter.lastRequest!;

      expect(request.method, 'PUT');
      expect(request.uri.path, '/api/v1/users/me/password');
      expect(request.data, <String, String>{
        'current_password': 'Password123',
        'new_password': 'NewPassword456',
      });
    });

    test('sends account deactivation request', () async {
      final adapter = _RecordingAdapter(
        responseData: <String, Object?>{
          'success': true,
          'message': 'Account deactivated successfully',
        },
      );

      final remote = _remote(adapter);

      await remote.deactivateAccount();

      final request = adapter.lastRequest!;

      expect(request.method, 'DELETE');
      expect(request.uri.path, '/api/v1/users/me');
    });

    test('preserves profile conflict status and message', () async {
      final adapter = _RecordingAdapter(
        statusCode: 409,
        responseData: <String, Object?>{'detail': 'Email already in use'},
      );

      final remote = _remote(adapter);

      await expectLater(
        remote.updateProfile(
          fullName: 'Updated User',
          email: 'existing@example.com',
        ),
        throwsA(
          isA<AppException>()
              .having((error) => error.statusCode, 'statusCode', 409)
              .having(
                (error) => error.message,
                'message',
                'Email already in use',
              ),
        ),
      );
    });
  });
}

DioAuthRemoteDataSource _remote(_RecordingAdapter adapter) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1'));

  dio.httpClientAdapter = adapter;

  return DioAuthRemoteDataSource(
    BackendDioClient(tokenStorage: _MemoryTokenStorage('test-token'), dio: dio),
  );
}

Map<String, Object?> _userEnvelope({
  required String fullName,
  required String email,
}) {
  return <String, Object?>{
    'success': true,
    'message': 'User profile updated successfully',
    'data': <String, Object?>{
      'id': 7,
      'full_name': fullName,
      'email': email,
      'is_active': true,
      'created_at': '2026-07-31T00:00:00+00:00',
    },
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
