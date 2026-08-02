import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/alerts/data/backend_price_alert.dart';
import 'package:p_trader_ai/features/alerts/data/price_alert_remote_data_source.dart';

void main() {
  group('DioPriceAlertRemoteDataSource', () {
    test('lists backend price alerts', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{
          'success': true,
          'message': 'Alerts retrieved successfully',
          'data': <Map<String, dynamic>>[_alertJson()],
        },
      );

      final alerts = await harness.source.listAlerts();

      expect(alerts, hasLength(1));
      expect(alerts.single.id, 9);
      expect(harness.adapter.lastRequest?.method, 'GET');
      expect(harness.adapter.lastRequest?.path, '/alerts');
    });

    test('creates a normalized Bybit price alert', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{
          'success': true,
          'message': 'Alert created successfully',
          'data': _alertJson(),
        },
      );

      final alert = await harness.source.createAlert(
        symbol: 'btc',
        exchange: 'bybit',
        condition: BackendPriceAlertCondition.above,
        targetPrice: 120000,
      );

      final body = Map<String, dynamic>.from(
        harness.adapter.lastRequest?.data as Map,
      );

      expect(alert.symbol, 'BTCUSDT');
      expect(body['symbol'], 'BTCUSDT');
      expect(body['exchange'], 'BYBIT');
      expect(body['alert_type'], 'PRICE_ABOVE');
      expect(body['target_value'], 120000);
    });

    test('sends partial update booleans correctly', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{
          'success': true,
          'message': 'Alert updated successfully',
          'data': _alertJson(isEnabled: false, triggered: true),
        },
      );

      final alert = await harness.source.updateAlert(
        alertId: 9,
        isEnabled: false,
        triggered: true,
      );

      final body = Map<String, dynamic>.from(
        harness.adapter.lastRequest?.data as Map,
      );

      expect(alert.isEnabled, isFalse);
      expect(alert.triggered, isTrue);
      expect(body, <String, dynamic>{'is_enabled': false, 'triggered': true});
      expect(harness.adapter.lastRequest?.path, '/alerts/9');
    });

    test('deletes by backend alert ID', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{
          'success': true,
          'message': 'Alert deleted successfully',
          'data': null,
        },
      );

      await harness.source.deleteAlert(9);

      expect(harness.adapter.lastRequest?.method, 'DELETE');
      expect(harness.adapter.lastRequest?.path, '/alerts/9');
    });

    test('preserves backend not-found details', () async {
      final harness = _Harness(
        statusCode: 404,
        responseData: <String, dynamic>{'detail': 'Alert not found'},
      );

      await expectLater(
        harness.source.getAlert(999),
        throwsA(
          isA<AppException>()
              .having((error) => error.message, 'message', 'Alert not found')
              .having((error) => error.statusCode, 'statusCode', 404),
        ),
      );
    });

    test('rejects invalid target prices locally', () async {
      final harness = _Harness(
        statusCode: 200,
        responseData: <String, dynamic>{'success': true, 'data': _alertJson()},
      );

      await expectLater(
        harness.source.createAlert(
          symbol: 'BTC',
          exchange: 'BYBIT',
          condition: BackendPriceAlertCondition.above,
          targetPrice: double.nan,
        ),
        throwsA(isA<AppException>()),
      );

      expect(harness.adapter.lastRequest, isNull);
    });
  });
}

Map<String, dynamic> _alertJson({
  bool isEnabled = true,
  bool triggered = false,
}) {
  return <String, dynamic>{
    'id': 9,
    'user_id': 7,
    'symbol': 'BTCUSDT',
    'exchange': 'BYBIT',
    'alert_type': 'PRICE_ABOVE',
    'target_value': 120000,
    'is_enabled': isEnabled,
    'triggered': triggered,
    'created_at': '2026-08-02T20:00:00Z',
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
    source = DioPriceAlertRemoteDataSource(dio);
  }

  final Dio dio;
  final _StaticHttpClientAdapter adapter;
  late final DioPriceAlertRemoteDataSource source;
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
