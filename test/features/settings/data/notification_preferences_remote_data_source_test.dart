import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/settings/data/backend_notification_preferences.dart';
import 'package:p_trader_ai/features/settings/data/notification_preferences_remote_data_source.dart';

void main() {
  group('DioNotificationPreferencesRemoteDataSource', () {
    test('gets authenticated preferences', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{
          'success': true,
          'message': 'Notification preferences retrieved successfully',
          'data': _preferencesJson(),
        },
      );

      final preferences = await harness.source.getPreferences();

      expect(preferences.id, 4);
      expect(harness.adapter.lastRequest?.method, 'GET');
      expect(harness.adapter.lastRequest?.path, '/notification-preferences');
    });

    test('updates only supplied fields', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{
          'success': true,
          'message': 'Notification preferences updated successfully',
          'data': _preferencesJson(pushEnabled: false, newsAlerts: true),
        },
      );

      final preferences = await harness.source.updatePreferences(
        const NotificationPreferenceUpdate(
          pushEnabled: false,
          newsAlerts: true,
        ),
      );

      final body = Map<String, dynamic>.from(
        harness.adapter.lastRequest?.data as Map,
      );

      expect(preferences.pushEnabled, isFalse);
      expect(preferences.newsAlerts, isTrue);
      expect(harness.adapter.lastRequest?.method, 'PUT');
      expect(harness.adapter.lastRequest?.path, '/notification-preferences');
      expect(body, <String, dynamic>{
        'push_enabled': false,
        'news_alerts': true,
      });
    });

    test('preserves backend error details', () async {
      final harness = _Harness(
        statusCode: 401,
        responseData: <String, dynamic>{'detail': 'Invalid or expired token'},
      );

      await expectLater(
        harness.source.getPreferences(),
        throwsA(
          isA<AppException>()
              .having(
                (error) => error.message,
                'message',
                'Invalid or expired token',
              )
              .having((error) => error.statusCode, 'statusCode', 401),
        ),
      );
    });

    test('rejects non-map preference data', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{'success': true, 'data': <Object?>[]},
      );

      await expectLater(
        harness.source.getPreferences(),
        throwsA(isA<AppException>()),
      );
    });

    test('rejects invalid preference fields', () async {
      final invalid = _preferencesJson();
      invalid['push_enabled'] = 'yes';

      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{'success': true, 'data': invalid},
      );

      await expectLater(
        harness.source.getPreferences(),
        throwsA(isA<AppException>()),
      );
    });

    test('rejects empty updates locally', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{
          'success': true,
          'data': _preferencesJson(),
        },
      );

      await expectLater(
        harness.source.updatePreferences(const NotificationPreferenceUpdate()),
        throwsA(isA<AppException>()),
      );

      expect(harness.adapter.lastRequest, isNull);
    });
  });
}

Map<String, dynamic> _preferencesJson({
  bool pushEnabled = true,
  bool newsAlerts = false,
}) {
  return <String, dynamic>{
    'id': 4,
    'user_id': 9,
    'email_enabled': true,
    'push_enabled': pushEnabled,
    'sound_enabled': true,
    'price_alerts': true,
    'arbitrage_alerts': true,
    'ai_alerts': true,
    'news_alerts': newsAlerts,
    'updated_at': '2026-08-03T00:00:00Z',
  };
}

class _Harness {
  _Harness({required int statusCode, required Object? responseData})
    : adapter = _StaticHttpClientAdapter(
        statusCode: statusCode,
        responseData: responseData,
      ),
      dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1')) {
    dio.httpClientAdapter = adapter;

    source = DioNotificationPreferencesRemoteDataSource(dio);
  }

  final Dio dio;
  final _StaticHttpClientAdapter adapter;

  late final DioNotificationPreferencesRemoteDataSource source;
}

class _StaticHttpClientAdapter implements HttpClientAdapter {
  _StaticHttpClientAdapter({
    required this.statusCode,
    required this.responseData,
  });

  final int statusCode;
  final Object? responseData;

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
