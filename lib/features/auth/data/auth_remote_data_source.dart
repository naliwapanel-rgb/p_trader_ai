import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/network/backend_dio_client.dart';
import 'auth_token.dart';

abstract interface class AuthRemoteDataSource {
  Future<AuthToken> login({required String email, required String password});
}

class DioAuthRemoteDataSource implements AuthRemoteDataSource {
  const DioAuthRemoteDataSource(this._client);

  final BackendDioClient _client;

  @override
  Future<AuthToken> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _client.dio.post<Object?>(
        '/auth/login',
        data: <String, String>{'email': email.trim(), 'password': password},
      );

      final data = response.data;

      if (data is! Map) {
        throw const AppException(
          'The authentication server returned an invalid response.',
        );
      }

      return AuthToken.fromJson(Map<String, dynamic>.from(data));
    } on DioException catch (error) {
      throw AppException(
        _extractErrorMessage(error),
        statusCode: error.response?.statusCode,
      );
    } on FormatException catch (error) {
      throw AppException(error.message);
    } on AppException {
      rethrow;
    } catch (_) {
      throw const AppException('An unexpected authentication error occurred.');
    }
  }

  String _extractErrorMessage(DioException error) {
    final statusCode = error.response?.statusCode;
    final data = error.response?.data;

    final serverMessage = _extractServerMessage(data);

    if (serverMessage != null) {
      return serverMessage;
    }

    return switch (statusCode) {
      400 => 'The login request was rejected.',
      401 => 'Incorrect email or password.',
      403 => 'This account is not permitted to sign in.',
      422 => 'Check your email and password, then try again.',
      429 => 'Too many login attempts. Try again later.',
      int code when code >= 500 =>
        'The authentication service is temporarily unavailable.',
      _ => _networkMessage(error.type),
    };
  }

  String? _extractServerMessage(Object? data) {
    if (data is! Map) {
      return null;
    }

    final detail = data['detail'];

    if (detail is String && detail.trim().isNotEmpty) {
      return detail.trim();
    }

    if (detail is List) {
      final messages = detail
          .whereType<Map>()
          .map((entry) => entry['msg'])
          .whereType<String>()
          .where((message) => message.trim().isNotEmpty)
          .map((message) => message.trim())
          .toList();

      if (messages.isNotEmpty) {
        return messages.join('\n');
      }
    }

    return null;
  }

  String _networkMessage(DioExceptionType type) {
    return switch (type) {
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout =>
        'The connection timed out. Check the backend and try again.',
      DioExceptionType.connectionError =>
        'Unable to connect to the P-TRADER AI backend.',
      DioExceptionType.badCertificate =>
        'The backend security certificate could not be verified.',
      DioExceptionType.cancel => 'The login request was cancelled.',
      _ => 'Login failed. Check your connection and try again.',
    };
  }
}
