import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import 'backend_notification_preferences.dart';

abstract interface class NotificationPreferencesRemoteDataSource {
  Future<BackendNotificationPreferences> getPreferences();

  Future<BackendNotificationPreferences> updatePreferences(
    NotificationPreferenceUpdate update,
  );
}

class DioNotificationPreferencesRemoteDataSource
    implements NotificationPreferencesRemoteDataSource {
  const DioNotificationPreferencesRemoteDataSource(this._dio);

  final Dio _dio;

  @override
  Future<BackendNotificationPreferences> getPreferences() async {
    final envelope = await _performRequest(
      () => _dio.get<Object?>('/notification-preferences'),
      invalidResponseMessage:
          'The notification-preference service returned '
          'an invalid response.',
    );

    return _parsePreferences(
      envelope['data'],
      'The notification preferences are invalid.',
    );
  }

  @override
  Future<BackendNotificationPreferences> updatePreferences(
    NotificationPreferenceUpdate update,
  ) async {
    if (!update.hasChanges) {
      throw const AppException(
        'At least one notification preference must be supplied.',
      );
    }

    final envelope = await _performRequest(
      () =>
          _dio.put<Object?>('/notification-preferences', data: update.toJson()),
      invalidResponseMessage:
          'The updated notification preferences are invalid.',
    );

    return _parsePreferences(
      envelope['data'],
      'The updated notification preferences are invalid.',
    );
  }

  BackendNotificationPreferences _parsePreferences(
    Object? value,
    String invalidMessage,
  ) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return BackendNotificationPreferences.fromJson(
        Map<String, dynamic>.from(value),
      );
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  Future<Map<String, dynamic>> _performRequest(
    Future<Response<Object?>> Function() request, {
    required String invalidResponseMessage,
  }) async {
    try {
      final response = await request();
      final body = response.data;

      if (body is! Map) {
        throw AppException(invalidResponseMessage);
      }

      final envelope = Map<String, dynamic>.from(body);
      final success = envelope['success'];

      if (success is bool && !success) {
        throw AppException(
          _extractServerMessage(envelope) ?? invalidResponseMessage,
          statusCode: response.statusCode,
        );
      }

      return envelope;
    } on DioException catch (error) {
      throw _toAppException(error);
    } on AppException {
      rethrow;
    } catch (_) {
      throw AppException(invalidResponseMessage);
    }
  }

  AppException _toAppException(DioException error) {
    return AppException(
      _extractServerMessage(error.response?.data) ??
          _networkMessage(error.type),
      statusCode: error.response?.statusCode,
    );
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

    if (detail is List && detail.isNotEmpty) {
      final first = detail.first;

      if (first is Map) {
        final validationMessage = first['msg'];

        if (validationMessage is String &&
            validationMessage.trim().isNotEmpty) {
          return validationMessage.trim();
        }
      }
    }

    return null;
  }

  String _networkMessage(DioExceptionType type) {
    switch (type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return 'The notification-preference request timed out.';
      case DioExceptionType.connectionError:
        return 'The notification-preference service could not be reached.';
      case DioExceptionType.badCertificate:
        return 'The notification-preference service certificate is invalid.';
      case DioExceptionType.cancel:
        return 'The notification-preference request was cancelled.';
      case DioExceptionType.badResponse:
        return 'The notification-preference request failed.';
      case DioExceptionType.unknown:
        return 'The notification-preference request failed unexpectedly.';
    }
  }
}
