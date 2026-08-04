import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import '../../bots/data/backend_trading_bot.dart';
import 'backend_strategy_template.dart';

abstract interface class StrategyTemplateRemoteDataSource {
  Future<List<BackendStrategyTemplate>> listOwned({
    StrategyTemplateStatus? status,
    StrategyTemplateVisibility? visibility,
    int limit = 50,
    int offset = 0,
  });

  Future<List<BackendStrategyTemplate>> listPublic({
    int limit = 50,
    int offset = 0,
  });

  Future<BackendStrategyTemplate> getTemplate(int templateId);

  Future<BackendStrategyTemplate> createTemplate(
    StrategyTemplateCreateRequest request,
  );

  Future<BackendStrategyTemplate> updateTemplate({
    required int templateId,
    required StrategyTemplateUpdateRequest request,
  });

  Future<void> deleteTemplate(int templateId);

  Future<StrategyTemplateActionResult> performAction({
    required int templateId,
    required StrategyTemplateAction action,
  });

  Future<BackendTradingBot> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  });
}

class DioStrategyTemplateRemoteDataSource
    implements StrategyTemplateRemoteDataSource {
  const DioStrategyTemplateRemoteDataSource(this._dio);

  final Dio _dio;

  @override
  Future<List<BackendStrategyTemplate>> listOwned({
    StrategyTemplateStatus? status,
    StrategyTemplateVisibility? visibility,
    int limit = 50,
    int offset = 0,
  }) async {
    _validatePagination(limit: limit, offset: offset);

    final envelope = await _performRequest(
      () => _dio.get<Object?>(
        '/strategy-templates',
        queryParameters: <String, dynamic>{
          if (status != null) 'status': status.backendValue,
          if (visibility != null) 'visibility': visibility.backendValue,
          'limit': limit,
          'offset': offset,
        },
      ),
      invalidResponseMessage:
          'The strategy-template service returned an invalid list.',
    );

    return _parseTemplateList(envelope['data']);
  }

  @override
  Future<List<BackendStrategyTemplate>> listPublic({
    int limit = 50,
    int offset = 0,
  }) async {
    _validatePagination(limit: limit, offset: offset);

    final envelope = await _performRequest(
      () => _dio.get<Object?>(
        '/strategy-templates/public',
        queryParameters: <String, dynamic>{'limit': limit, 'offset': offset},
      ),
      invalidResponseMessage:
          'The public strategy-template service returned an invalid list.',
    );

    return _parseTemplateList(envelope['data']);
  }

  @override
  Future<BackendStrategyTemplate> getTemplate(int templateId) async {
    _validateTemplateId(templateId);

    final envelope = await _performRequest(
      () => _dio.get<Object?>('/strategy-templates/$templateId'),
      invalidResponseMessage: 'The requested strategy template is invalid.',
    );

    return _parseTemplate(
      envelope['data'],
      'The requested strategy template is invalid.',
    );
  }

  @override
  Future<BackendStrategyTemplate> createTemplate(
    StrategyTemplateCreateRequest request,
  ) async {
    final payload = _serializeCreate(request);

    final envelope = await _performRequest(
      () => _dio.post<Object?>('/strategy-templates', data: payload),
      invalidResponseMessage: 'The created strategy template is invalid.',
    );

    return _parseTemplate(
      envelope['data'],
      'The created strategy template is invalid.',
    );
  }

  @override
  Future<BackendStrategyTemplate> updateTemplate({
    required int templateId,
    required StrategyTemplateUpdateRequest request,
  }) async {
    _validateTemplateId(templateId);

    final payload = _serializeUpdate(request);

    final envelope = await _performRequest(
      () => _dio.put<Object?>('/strategy-templates/$templateId', data: payload),
      invalidResponseMessage: 'The updated strategy template is invalid.',
    );

    return _parseTemplate(
      envelope['data'],
      'The updated strategy template is invalid.',
    );
  }

  @override
  Future<void> deleteTemplate(int templateId) async {
    _validateTemplateId(templateId);

    await _performRequest(
      () => _dio.delete<Object?>('/strategy-templates/$templateId'),
      invalidResponseMessage: 'The strategy template could not be deleted.',
    );
  }

  @override
  Future<StrategyTemplateActionResult> performAction({
    required int templateId,
    required StrategyTemplateAction action,
  }) async {
    _validateTemplateId(templateId);

    final envelope = await _performRequest(
      () => _dio.post<Object?>(
        '/strategy-templates/'
        '$templateId/${action.routeValue}',
      ),
      invalidResponseMessage:
          'The strategy-template action response is invalid.',
    );

    final data = envelope['data'];

    if (data is! Map) {
      throw const AppException(
        'The strategy-template action response is invalid.',
      );
    }

    try {
      return StrategyTemplateActionResult.fromJson(
        Map<String, dynamic>.from(data),
      );
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  @override
  Future<BackendTradingBot> createBotFromTemplate({
    required int templateId,
    required StrategyTemplateBotCreateRequest request,
  }) async {
    _validateTemplateId(templateId);

    final payload = _serializeBotCreate(request);

    final envelope = await _performRequest(
      () => _dio.post<Object?>(
        '/strategy-templates/$templateId/create-bot',
        data: payload,
      ),
      invalidResponseMessage: 'The template-created trading bot is invalid.',
    );

    final data = envelope['data'];

    if (data is! Map) {
      throw const AppException('The template-created trading bot is invalid.');
    }

    try {
      return BackendTradingBot.fromJson(Map<String, dynamic>.from(data));
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  List<BackendStrategyTemplate> _parseTemplateList(Object? value) {
    if (value is! List) {
      throw const AppException(
        'The strategy-template service returned an invalid list.',
      );
    }

    try {
      return value
          .map((entry) {
            if (entry is! Map) {
              throw const FormatException(
                'A strategy-template entry is invalid.',
              );
            }

            return BackendStrategyTemplate.fromJson(
              Map<String, dynamic>.from(entry),
            );
          })
          .toList(growable: false);
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  BackendStrategyTemplate _parseTemplate(Object? value, String invalidMessage) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return BackendStrategyTemplate.fromJson(Map<String, dynamic>.from(value));
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  Map<String, Object?> _serializeCreate(StrategyTemplateCreateRequest request) {
    try {
      return request.toJson();
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  Map<String, Object?> _serializeUpdate(StrategyTemplateUpdateRequest request) {
    try {
      return request.toJson();
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  Map<String, Object?> _serializeBotCreate(
    StrategyTemplateBotCreateRequest request,
  ) {
    try {
      return request.toJson();
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

    if (detail is List) {
      final messages = detail
          .whereType<Map>()
          .map((entry) => entry['msg'])
          .whereType<String>()
          .where((item) => item.trim().isNotEmpty)
          .map((item) => item.trim())
          .toList(growable: false);

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
        'The strategy-template request timed out.',
      DioExceptionType.connectionError =>
        'Unable to connect to the P-TRADER AI backend.',
      DioExceptionType.badCertificate =>
        'The backend security certificate could not be verified.',
      DioExceptionType.cancel => 'The strategy-template request was cancelled.',
      _ => 'The strategy-template request failed.',
    };
  }

  void _validatePagination({required int limit, required int offset}) {
    if (limit < 1 || limit > 200) {
      throw const AppException(
        'The strategy-template limit must be between 1 and 200.',
      );
    }

    if (offset < 0) {
      throw const AppException(
        'The strategy-template offset cannot be negative.',
      );
    }
  }

  void _validateTemplateId(int templateId) {
    if (templateId <= 0) {
      throw const AppException('The strategy-template ID must be positive.');
    }
  }
}
