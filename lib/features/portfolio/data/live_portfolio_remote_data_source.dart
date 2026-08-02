import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/network/backend_dio_client.dart';
import 'backend_portfolio.dart';
import 'portfolio_sync_result.dart';
import 'portfolio_sync_snapshot.dart';

abstract interface class LivePortfolioRemoteDataSource {
  Future<List<BackendPortfolio>> listPortfolios();

  Future<BackendPortfolio> createPortfolio({
    required String name,
    required String baseCurrency,
  });

  Future<PortfolioSyncResult> synchronize({
    required int portfolioId,
    required int exchangeAccountId,
    required String category,
    required String settleCoin,
  });

  Future<PortfolioSyncSnapshot> getLatestSnapshot({
    required int portfolioId,
    int? exchangeAccountId,
  });

  Future<List<PortfolioSyncSnapshot>> listSyncHistory({
    required int portfolioId,
    int limit = 50,
  });
}

class DioLivePortfolioRemoteDataSource
    implements LivePortfolioRemoteDataSource {
  const DioLivePortfolioRemoteDataSource(this._client);

  final BackendDioClient _client;

  @override
  Future<List<BackendPortfolio>> listPortfolios() async {
    final envelope = await _performRequest(
      () => _client.dio.get<Object?>('/portfolios'),
      invalidResponseMessage: 'The portfolio service returned an invalid list.',
    );

    final data = envelope['data'];

    if (data is! List) {
      throw const AppException(
        'The portfolio service returned an invalid list.',
      );
    }

    try {
      return data
          .map((entry) {
            if (entry is! Map) {
              throw const FormatException('A portfolio entry is invalid.');
            }

            return BackendPortfolio.fromJson(Map<String, dynamic>.from(entry));
          })
          .toList(growable: false);
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  @override
  Future<BackendPortfolio> createPortfolio({
    required String name,
    required String baseCurrency,
  }) async {
    final envelope = await _performRequest(
      () => _client.dio.post<Object?>(
        '/portfolios',
        data: <String, Object>{
          'name': name.trim(),
          'base_currency': baseCurrency.trim().toUpperCase(),
        },
      ),
      invalidResponseMessage: 'The backend portfolio could not be created.',
    );

    return _parsePortfolio(
      envelope['data'],
      'The created backend portfolio is invalid.',
    );
  }

  @override
  Future<PortfolioSyncResult> synchronize({
    required int portfolioId,
    required int exchangeAccountId,
    required String category,
    required String settleCoin,
  }) async {
    final envelope = await _performRequest(
      () => _client.dio.post<Object?>(
        '/portfolios/$portfolioId/sync',
        data: <String, Object>{
          'exchange_account_id': exchangeAccountId,
          'category': category.trim().toLowerCase(),
          'settle_coin': settleCoin.trim().toUpperCase(),
        },
      ),
      invalidResponseMessage: 'The portfolio synchronization failed.',
    );

    final data = envelope['data'];

    if (data is! Map) {
      throw const AppException(
        'The portfolio synchronization result is invalid.',
      );
    }

    try {
      return PortfolioSyncResult.fromJson(Map<String, dynamic>.from(data));
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  @override
  Future<PortfolioSyncSnapshot> getLatestSnapshot({
    required int portfolioId,
    int? exchangeAccountId,
  }) async {
    final queryParameters = <String, Object>{};

    if (exchangeAccountId != null) {
      queryParameters['exchange_account_id'] = exchangeAccountId;
    }

    final envelope = await _performRequest(
      () => _client.dio.get<Object?>(
        '/portfolios/$portfolioId/sync/latest',
        queryParameters: queryParameters,
      ),
      invalidResponseMessage:
          'The latest portfolio synchronization is invalid.',
    );

    return _parseSnapshot(
      envelope['data'],
      'The latest portfolio synchronization is invalid.',
    );
  }

  @override
  Future<List<PortfolioSyncSnapshot>> listSyncHistory({
    required int portfolioId,
    int limit = 50,
  }) async {
    final envelope = await _performRequest(
      () => _client.dio.get<Object?>(
        '/portfolios/$portfolioId/sync/history',
        queryParameters: <String, Object>{'limit': limit},
      ),
      invalidResponseMessage:
          'The portfolio synchronization history is invalid.',
    );

    final data = envelope['data'];

    if (data is! List) {
      throw const AppException(
        'The portfolio synchronization history is invalid.',
      );
    }

    try {
      return data
          .map((entry) {
            if (entry is! Map) {
              throw const FormatException(
                'A portfolio synchronization entry is invalid.',
              );
            }

            return PortfolioSyncSnapshot.fromJson(
              Map<String, dynamic>.from(entry),
            );
          })
          .toList(growable: false);
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  BackendPortfolio _parsePortfolio(Object? value, String invalidMessage) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return BackendPortfolio.fromJson(Map<String, dynamic>.from(value));
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  PortfolioSyncSnapshot _parseSnapshot(Object? value, String invalidMessage) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return PortfolioSyncSnapshot.fromJson(Map<String, dynamic>.from(value));
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
          .where((entry) => entry.trim().isNotEmpty)
          .map((entry) => entry.trim())
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
        'The portfolio request timed out. Try again.',
      DioExceptionType.connectionError =>
        'Unable to connect to the P-TRADER AI backend.',
      DioExceptionType.badCertificate =>
        'The backend security certificate could not be verified.',
      DioExceptionType.cancel => 'The portfolio request was cancelled.',
      _ => 'The portfolio request failed. Check the connection and try again.',
    };
  }
}
