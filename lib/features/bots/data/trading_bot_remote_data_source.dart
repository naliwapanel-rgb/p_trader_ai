import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import 'backend_trading_bot.dart';

abstract interface class TradingBotRemoteDataSource {
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  });

  Future<BackendTradingBot> getBot(int botId);

  Future<BackendTradingBot> createBot(TradingBotCreateRequest request);

  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  });

  Future<void> deleteBot(int botId);

  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  });
}

class DioTradingBotRemoteDataSource implements TradingBotRemoteDataSource {
  const DioTradingBotRemoteDataSource(this._dio);

  final Dio _dio;

  @override
  Future<List<BackendTradingBot>> listBots({
    TradingBotStatus? status,
    int limit = 50,
    int offset = 0,
  }) async {
    if (limit < 1 || limit > 200) {
      throw const AppException(
        'The trading-bot limit must be between 1 and 200.',
      );
    }

    if (offset < 0) {
      throw const AppException('The trading-bot offset cannot be negative.');
    }

    final envelope = await _performRequest(
      () => _dio.get<Object?>(
        '/trading-bots',
        queryParameters: <String, Object>{
          if (status != null) 'status': status.backendValue,
          'limit': limit,
          'offset': offset,
        },
      ),
      invalidResponseMessage:
          'The trading-bot service returned an invalid list.',
    );

    final data = envelope['data'];

    if (data is! List) {
      throw const AppException(
        'The trading-bot service returned an invalid list.',
      );
    }

    try {
      return data
          .map((entry) {
            if (entry is! Map) {
              throw const FormatException('A trading-bot entry is invalid.');
            }

            return BackendTradingBot.fromJson(Map<String, dynamic>.from(entry));
          })
          .toList(growable: false);
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  @override
  Future<BackendTradingBot> getBot(int botId) async {
    _validateBotId(botId);

    final envelope = await _performRequest(
      () => _dio.get<Object?>('/trading-bots/$botId'),
      invalidResponseMessage: 'The requested trading bot is invalid.',
    );

    return _parseBot(envelope['data'], 'The requested trading bot is invalid.');
  }

  @override
  Future<BackendTradingBot> createBot(TradingBotCreateRequest request) async {
    final payload = _serializeCreate(request);

    final envelope = await _performRequest(
      () => _dio.post<Object?>('/trading-bots', data: payload),
      invalidResponseMessage: 'The created trading bot is invalid.',
    );

    return _parseBot(envelope['data'], 'The created trading bot is invalid.');
  }

  @override
  Future<BackendTradingBot> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  }) async {
    _validateBotId(botId);

    final payload = _serializeUpdate(request);

    final envelope = await _performRequest(
      () => _dio.put<Object?>('/trading-bots/$botId', data: payload),
      invalidResponseMessage: 'The updated trading bot is invalid.',
    );

    return _parseBot(envelope['data'], 'The updated trading bot is invalid.');
  }

  @override
  Future<void> deleteBot(int botId) async {
    _validateBotId(botId);

    await _performRequest(
      () => _dio.delete<Object?>('/trading-bots/$botId'),
      invalidResponseMessage: 'The trading bot could not be deleted.',
    );
  }

  @override
  Future<TradingBotLifecycleResult> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) async {
    _validateBotId(botId);

    final envelope = await _performRequest(
      () => _dio.post<Object?>('/trading-bots/$botId/${action.routeValue}'),
      invalidResponseMessage: 'The trading-bot lifecycle response is invalid.',
    );

    final data = envelope['data'];

    if (data is! Map) {
      throw const AppException(
        'The trading-bot lifecycle response is invalid.',
      );
    }

    try {
      return TradingBotLifecycleResult.fromJson(
        Map<String, dynamic>.from(data),
      );
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  Map<String, Object?> _serializeCreate(TradingBotCreateRequest request) {
    try {
      return request.toJson();
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  Map<String, Object?> _serializeUpdate(TradingBotUpdateRequest request) {
    try {
      return request.toJson();
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  BackendTradingBot _parseBot(Object? value, String invalidMessage) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return BackendTradingBot.fromJson(Map<String, dynamic>.from(value));
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

      if (envelope['success'] == false) {
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
    return switch (type) {
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout => 'The trading-bot request timed out.',
      DioExceptionType.connectionError =>
        'The trading-bot service could not be reached.',
      DioExceptionType.badCertificate =>
        'The trading-bot service certificate is invalid.',
      DioExceptionType.cancel => 'The trading-bot request was cancelled.',
      DioExceptionType.badResponse => 'The trading-bot request failed.',
      DioExceptionType.unknown =>
        'The trading-bot request failed unexpectedly.',
    };
  }

  void _validateBotId(int botId) {
    if (botId <= 0) {
      throw const AppException('The trading-bot ID is invalid.');
    }
  }
}
