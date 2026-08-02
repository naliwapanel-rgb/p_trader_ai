import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import 'backend_price_alert.dart';

abstract interface class PriceAlertRemoteDataSource {
  Future<List<BackendPriceAlert>> listAlerts();

  Future<BackendPriceAlert> getAlert(int alertId);

  Future<BackendPriceAlert> createAlert({
    required String symbol,
    required String exchange,
    required BackendPriceAlertCondition condition,
    required double targetPrice,
  });

  Future<BackendPriceAlert> updateAlert({
    required int alertId,
    String? symbol,
    String? exchange,
    BackendPriceAlertCondition? condition,
    double? targetPrice,
    bool? isEnabled,
    bool? triggered,
  });

  Future<void> deleteAlert(int alertId);
}

class DioPriceAlertRemoteDataSource implements PriceAlertRemoteDataSource {
  const DioPriceAlertRemoteDataSource(this._dio);

  final Dio _dio;

  @override
  Future<List<BackendPriceAlert>> listAlerts() async {
    final envelope = await _performRequest(
      () => _dio.get<Object?>('/alerts'),
      invalidResponseMessage:
          'The price-alert service returned an invalid list.',
    );

    final data = envelope['data'];

    if (data is! List) {
      throw const AppException(
        'The price-alert service returned an invalid list.',
      );
    }

    try {
      return data
          .map((entry) {
            if (entry is! Map) {
              throw const FormatException('A price-alert entry is invalid.');
            }

            return BackendPriceAlert.fromJson(Map<String, dynamic>.from(entry));
          })
          .toList(growable: false);
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  @override
  Future<BackendPriceAlert> getAlert(int alertId) async {
    _validateAlertId(alertId);

    final envelope = await _performRequest(
      () => _dio.get<Object?>('/alerts/$alertId'),
      invalidResponseMessage: 'The requested price alert is invalid.',
    );

    return _parseAlert(
      envelope['data'],
      'The requested price alert is invalid.',
    );
  }

  @override
  Future<BackendPriceAlert> createAlert({
    required String symbol,
    required String exchange,
    required BackendPriceAlertCondition condition,
    required double targetPrice,
  }) async {
    final normalizedSymbol = PriceAlertSymbolMapper.toTradingPair(symbol);
    final normalizedExchange = _normalizeExchange(exchange);

    _validateTargetPrice(targetPrice);

    final envelope = await _performRequest(
      () => _dio.post<Object?>(
        '/alerts',
        data: <String, Object>{
          'symbol': normalizedSymbol,
          'exchange': normalizedExchange,
          'alert_type': condition.backendValue,
          'target_value': targetPrice,
        },
      ),
      invalidResponseMessage: 'The created price alert is invalid.',
    );

    return _parseAlert(envelope['data'], 'The created price alert is invalid.');
  }

  @override
  Future<BackendPriceAlert> updateAlert({
    required int alertId,
    String? symbol,
    String? exchange,
    BackendPriceAlertCondition? condition,
    double? targetPrice,
    bool? isEnabled,
    bool? triggered,
  }) async {
    _validateAlertId(alertId);

    final data = <String, Object>{};

    if (symbol != null) {
      data['symbol'] = PriceAlertSymbolMapper.toTradingPair(symbol);
    }

    if (exchange != null) {
      data['exchange'] = _normalizeExchange(exchange);
    }

    if (condition != null) {
      data['alert_type'] = condition.backendValue;
    }

    if (targetPrice != null) {
      _validateTargetPrice(targetPrice);
      data['target_value'] = targetPrice;
    }

    if (isEnabled != null) {
      data['is_enabled'] = isEnabled;
    }

    if (triggered != null) {
      data['triggered'] = triggered;
    }

    if (data.isEmpty) {
      throw const AppException(
        'At least one price-alert field must be supplied.',
      );
    }

    final envelope = await _performRequest(
      () => _dio.put<Object?>('/alerts/$alertId', data: data),
      invalidResponseMessage: 'The updated price alert is invalid.',
    );

    return _parseAlert(envelope['data'], 'The updated price alert is invalid.');
  }

  @override
  Future<void> deleteAlert(int alertId) async {
    _validateAlertId(alertId);

    await _performRequest(
      () => _dio.delete<Object?>('/alerts/$alertId'),
      invalidResponseMessage: 'The price alert could not be deleted.',
    );
  }

  BackendPriceAlert _parseAlert(Object? value, String invalidMessage) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return BackendPriceAlert.fromJson(Map<String, dynamic>.from(value));
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
        return 'The price-alert request timed out.';
      case DioExceptionType.connectionError:
        return 'The price-alert service could not be reached.';
      case DioExceptionType.badCertificate:
        return 'The price-alert service certificate is invalid.';
      case DioExceptionType.cancel:
        return 'The price-alert request was cancelled.';
      case DioExceptionType.badResponse:
        return 'The price-alert request failed.';
      case DioExceptionType.unknown:
        return 'The price-alert request failed unexpectedly.';
    }
  }

  String _normalizeExchange(String value) {
    final normalized = value.trim().toUpperCase();

    if (normalized.length < 2 || normalized.length > 50) {
      throw const AppException('A valid exchange name is required.');
    }

    return normalized;
  }

  void _validateAlertId(int alertId) {
    if (alertId <= 0) {
      throw const AppException('The price-alert ID is invalid.');
    }
  }

  void _validateTargetPrice(double targetPrice) {
    if (!targetPrice.isFinite || targetPrice <= 0) {
      throw const AppException('The target price must be greater than zero.');
    }
  }
}
