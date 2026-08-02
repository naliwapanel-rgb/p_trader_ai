import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/network/backend_dio_client.dart';
import 'backend_watchlist_item.dart';

abstract interface class WatchlistRemoteDataSource {
  Future<List<BackendWatchlistItem>> listItems();

  Future<BackendWatchlistItem> createItem({
    required String symbol,
    required String exchange,
  });

  Future<void> deleteItem(int itemId);
}

class DioWatchlistRemoteDataSource implements WatchlistRemoteDataSource {
  const DioWatchlistRemoteDataSource(this._client);

  final BackendDioClient _client;

  @override
  Future<List<BackendWatchlistItem>> listItems() async {
    final envelope = await _performRequest(
      () => _client.dio.get<Object?>('/watchlists'),
      invalidResponseMessage: 'The watchlist service returned an invalid list.',
    );

    final data = envelope['data'];

    if (data is! List) {
      throw const AppException(
        'The watchlist service returned an invalid list.',
      );
    }

    try {
      return data
          .map((item) {
            if (item is! Map) {
              throw const FormatException('A watchlist entry is invalid.');
            }

            return BackendWatchlistItem.fromJson(
              Map<String, dynamic>.from(item),
            );
          })
          .toList(growable: false);
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  @override
  Future<BackendWatchlistItem> createItem({
    required String symbol,
    required String exchange,
  }) async {
    final normalizedSymbol = WatchlistSymbolMapper.toUsdtPair(symbol);

    final normalizedExchange = WatchlistSymbolMapper.normalizeExchange(
      exchange,
    );

    final envelope = await _performRequest(
      () => _client.dio.post<Object?>(
        '/watchlists',
        data: <String, Object>{
          'symbol': normalizedSymbol,
          'exchange': normalizedExchange,
        },
      ),
      invalidResponseMessage: 'The watchlist item could not be created.',
    );

    return _parseItem(
      envelope['data'],
      'The created watchlist item is invalid.',
    );
  }

  @override
  Future<void> deleteItem(int itemId) async {
    if (itemId <= 0) {
      throw const AppException('The watchlist item ID is invalid.');
    }

    await _performRequest(
      () => _client.dio.delete<Object?>('/watchlists/$itemId'),
      invalidResponseMessage: 'The watchlist item could not be deleted.',
    );
  }

  BackendWatchlistItem _parseItem(Object? value, String invalidMessage) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return BackendWatchlistItem.fromJson(Map<String, dynamic>.from(value));
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
      DioExceptionType.receiveTimeout => 'The watchlist request timed out.',
      DioExceptionType.connectionError =>
        'Unable to connect to the P-TRADER AI backend.',
      DioExceptionType.badCertificate =>
        'The backend security certificate could not be verified.',
      DioExceptionType.cancel => 'The watchlist request was cancelled.',
      _ => 'The watchlist request failed. Check the connection and try again.',
    };
  }
}
