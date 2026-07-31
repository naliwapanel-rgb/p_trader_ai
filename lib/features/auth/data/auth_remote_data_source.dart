import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/network/backend_dio_client.dart';
import 'auth_token.dart';
import 'auth_user.dart';

abstract interface class AuthRemoteDataSource {
  Future<AuthToken> login({required String email, required String password});

  Future<AuthUser> getCurrentUser();
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
      throw _toAppException(error);
    } on FormatException catch (error) {
      throw AppException(error.message);
    } on AppException {
      rethrow;
    } catch (_) {
      throw const AppException('An unexpected authentication error occurred.');
    }
  }

  @override
  Future<AuthUser> getCurrentUser() async {
    try {
      final response = await _client.dio.get<Object?>('/users/me');
      final responseBody = response.data;

      if (responseBody is! Map) {
        throw const AppException(
          'The user-profile service returned an invalid response.',
        );
      }

      final responseMap = Map<String, dynamic>.from(responseBody);
      final userData = responseMap['data'];

      if (userData is! Map) {
        throw const AppException(
          'The user-profile response did not contain user data.',
        );
      }

      return AuthUser.fromJson(Map<String, dynamic>.from(userData));
    } on DioException catch (error) {
      throw _toAppException(error);
    } on FormatException catch (error) {
      throw AppException(error.message);
    } on AppException {
      rethrow;
    } catch (_) {
      throw const AppException('An unexpected user-profile error occurred.');
    }
  }

  AppException _toAppException(DioException error) {
    return AppException(
      _extractErrorMessage(error),
      statusCode: error.response?.statusCode,
    );
  }

  String _extractErrorMessage(DioException error) {
    final statusCode = error.response?.statusCode;
    final serverMessage = _extractServerMessage(error.response?.data);

    if (serverMessage != null) {
      return serverMessage;
    }

    return switch (statusCode) {
      400 => 'The request was rejected by the server.',
      401 => 'Your session is invalid or has expired.',
      403 => 'This account is not permitted to continue.',
      422 => 'Check the submitted information and try again.',
      429 => 'Too many requests. Try again later.',
      int code when code >= 500 =>
        'The P-TRADER AI service is temporarily unavailable.',
      _ => _networkMessage(error.type),
    };
  }

  String? _extractServerMessage(Object? data) {
    if (data is! Map) {
      return null;
    }

    final message = data['message'];

    if (message is String && message.trim().isNotEmpty) {
      return message.trim();
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
          .where((item) => item.trim().isNotEmpty)
          .map((item) => item.trim())
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
      DioExceptionType.cancel => 'The request was cancelled.',
      _ => 'The request failed. Check your connection and try again.',
    };
  }
}
