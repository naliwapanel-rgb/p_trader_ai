import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/network/backend_dio_client.dart';
import 'auth_token.dart';
import 'auth_user.dart';

abstract interface class AuthRemoteDataSource {
  Future<AuthToken> register({
    required String fullName,
    required String email,
    required String password,
  });

  Future<AuthToken> login({required String email, required String password});

  Future<AuthUser> getCurrentUser();

  Future<AuthUser> updateProfile({
    required String fullName,
    required String email,
  });

  Future<void> updatePassword({
    required String currentPassword,
    required String newPassword,
  });

  Future<void> deactivateAccount();
}

class DioAuthRemoteDataSource implements AuthRemoteDataSource {
  const DioAuthRemoteDataSource(this._client);

  final BackendDioClient _client;

  @override
  Future<AuthToken> register({
    required String fullName,
    required String email,
    required String password,
  }) {
    return _requestToken(
      path: '/auth/register',
      data: <String, String>{
        'full_name': fullName.trim(),
        'email': email.trim().toLowerCase(),
        'password': password,
      },
    );
  }

  @override
  Future<AuthToken> login({required String email, required String password}) {
    return _requestToken(
      path: '/auth/login',
      data: <String, String>{
        'email': email.trim().toLowerCase(),
        'password': password,
      },
    );
  }

  Future<AuthToken> _requestToken({
    required String path,
    required Map<String, String> data,
  }) async {
    try {
      final response = await _client.dio.post<Object?>(path, data: data);

      final responseData = response.data;

      if (responseData is! Map) {
        throw const AppException(
          'The authentication server returned an invalid response.',
        );
      }

      return AuthToken.fromJson(Map<String, dynamic>.from(responseData));
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
  Future<AuthUser> getCurrentUser() {
    return _requestUser(
      request: () => _client.dio.get<Object?>('/users/me'),
      invalidResponseMessage:
          'The user-profile service returned an invalid response.',
      missingDataMessage:
          'The user-profile response did not contain user data.',
      unexpectedErrorMessage: 'An unexpected user-profile error occurred.',
    );
  }

  @override
  Future<AuthUser> updateProfile({
    required String fullName,
    required String email,
  }) {
    return _requestUser(
      request: () => _client.dio.put<Object?>(
        '/users/me',
        data: <String, String>{
          'full_name': fullName.trim(),
          'email': email.trim().toLowerCase(),
        },
      ),
      invalidResponseMessage:
          'The profile service returned an invalid response.',
      missingDataMessage:
          'The profile update response did not contain user data.',
      unexpectedErrorMessage: 'An unexpected profile update error occurred.',
    );
  }

  Future<AuthUser> _requestUser({
    required Future<Response<Object?>> Function() request,
    required String invalidResponseMessage,
    required String missingDataMessage,
    required String unexpectedErrorMessage,
  }) async {
    try {
      final response = await request();
      final responseBody = response.data;

      if (responseBody is! Map) {
        throw AppException(invalidResponseMessage);
      }

      final responseMap = Map<String, dynamic>.from(responseBody);

      final userData = responseMap['data'];

      if (userData is! Map) {
        throw AppException(missingDataMessage);
      }

      return AuthUser.fromJson(Map<String, dynamic>.from(userData));
    } on DioException catch (error) {
      throw _toAppException(error);
    } on FormatException catch (error) {
      throw AppException(error.message);
    } on AppException {
      rethrow;
    } catch (_) {
      throw AppException(unexpectedErrorMessage);
    }
  }

  @override
  Future<void> updatePassword({
    required String currentPassword,
    required String newPassword,
  }) {
    return _performAccountRequest(
      request: () => _client.dio.put<Object?>(
        '/users/me/password',
        data: <String, String>{
          'current_password': currentPassword,
          'new_password': newPassword,
        },
      ),
      unexpectedErrorMessage: 'An unexpected password update error occurred.',
    );
  }

  @override
  Future<void> deactivateAccount() {
    return _performAccountRequest(
      request: () => _client.dio.delete<Object?>('/users/me'),
      unexpectedErrorMessage:
          'An unexpected account deactivation error occurred.',
    );
  }

  Future<void> _performAccountRequest({
    required Future<Response<Object?>> Function() request,
    required String unexpectedErrorMessage,
  }) async {
    try {
      await request();
    } on DioException catch (error) {
      throw _toAppException(error);
    } on AppException {
      rethrow;
    } catch (_) {
      throw AppException(unexpectedErrorMessage);
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
      409 => 'An account with this email already exists.',
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
