import 'package:dio/dio.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/network/backend_dio_client.dart';
import 'exchange_account.dart';
import 'exchange_balance.dart';
import 'exchange_connection_result.dart';

abstract interface class ExchangeAccountRemoteDataSource {
  Future<List<ExchangeAccount>> listAccounts();

  Future<ExchangeAccount> createAccount({
    required String exchangeName,
    required String accountName,
    required String apiKey,
    required String apiSecret,
    required bool isTestnet,
  });

  Future<ExchangeAccount> updateAccount({
    required int accountId,
    String? accountName,
    String? apiKey,
    String? apiSecret,
    bool? isTestnet,
    bool? isActive,
  });

  Future<void> deleteAccount(int accountId);

  Future<ExchangeConnectionResult> testConnection(int accountId);

  Future<ExchangeBalance> getBalance(int accountId);
}

class DioExchangeAccountRemoteDataSource
    implements ExchangeAccountRemoteDataSource {
  const DioExchangeAccountRemoteDataSource(this._client);

  final BackendDioClient _client;

  @override
  Future<List<ExchangeAccount>> listAccounts() async {
    final envelope = await _performRequest(
      () => _client.dio.get<Object?>('/exchange-accounts'),
      invalidResponseMessage:
          'The exchange-account service returned an invalid list.',
    );

    final data = envelope['data'];

    if (data is! List) {
      throw const AppException(
        'The exchange-account service returned an invalid list.',
      );
    }

    try {
      return data
          .map((item) {
            if (item is! Map) {
              throw const FormatException(
                'An exchange account entry is invalid.',
              );
            }

            return ExchangeAccount.fromJson(Map<String, dynamic>.from(item));
          })
          .toList(growable: false);
    } on FormatException catch (error) {
      throw AppException(error.message);
    }
  }

  @override
  Future<ExchangeAccount> createAccount({
    required String exchangeName,
    required String accountName,
    required String apiKey,
    required String apiSecret,
    required bool isTestnet,
  }) async {
    final envelope = await _performRequest(
      () => _client.dio.post<Object?>(
        '/exchange-accounts',
        data: <String, Object>{
          'exchange_name': exchangeName.trim().toUpperCase(),
          'account_name': accountName.trim(),
          'api_key': apiKey.trim(),
          'api_secret': apiSecret.trim(),
          'is_testnet': isTestnet,
        },
      ),
      invalidResponseMessage: 'The exchange account could not be created.',
    );

    return _parseAccount(
      envelope['data'],
      'The created exchange account is invalid.',
    );
  }

  @override
  Future<ExchangeAccount> updateAccount({
    required int accountId,
    String? accountName,
    String? apiKey,
    String? apiSecret,
    bool? isTestnet,
    bool? isActive,
  }) async {
    final payload = <String, Object>{};

    if (accountName != null) {
      payload['account_name'] = accountName.trim();
    }

    if (apiKey != null) {
      payload['api_key'] = apiKey.trim();
    }

    if (apiSecret != null) {
      payload['api_secret'] = apiSecret.trim();
    }

    if (isTestnet != null) {
      payload['is_testnet'] = isTestnet;
    }

    if (isActive != null) {
      payload['is_active'] = isActive;
    }

    final envelope = await _performRequest(
      () => _client.dio.put<Object?>(
        '/exchange-accounts/$accountId',
        data: payload,
      ),
      invalidResponseMessage: 'The exchange account could not be updated.',
    );

    return _parseAccount(
      envelope['data'],
      'The updated exchange account is invalid.',
    );
  }

  @override
  Future<void> deleteAccount(int accountId) async {
    await _performRequest(
      () => _client.dio.delete<Object?>('/exchange-accounts/$accountId'),
      invalidResponseMessage: 'The exchange account could not be deleted.',
    );
  }

  @override
  Future<ExchangeConnectionResult> testConnection(int accountId) async {
    final envelope = await _performRequest(
      () => _client.dio.post<Object?>('/exchange-connections/$accountId/test'),
      invalidResponseMessage:
          'The exchange returned an invalid connection result.',
    );

    final data = envelope['data'];

    if (data is! Map) {
      throw const AppException(
        'The exchange returned an invalid connection result.',
      );
    }

    return ExchangeConnectionResult.fromJson(Map<String, dynamic>.from(data));
  }

  @override
  Future<ExchangeBalance> getBalance(int accountId) async {
    final envelope = await _performRequest(
      () =>
          _client.dio.get<Object?>('/exchange-connections/$accountId/balance'),
      invalidResponseMessage: 'The exchange returned an invalid balance.',
    );

    final data = envelope['data'];

    if (data is! Map) {
      throw const AppException('The exchange returned an invalid balance.');
    }

    return ExchangeBalance.fromJson(Map<String, dynamic>.from(data));
  }

  ExchangeAccount _parseAccount(Object? value, String invalidMessage) {
    if (value is! Map) {
      throw AppException(invalidMessage);
    }

    try {
      return ExchangeAccount.fromJson(Map<String, dynamic>.from(value));
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
        final message = _extractServerMessage(envelope);

        throw AppException(
          message ?? invalidResponseMessage,
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
    final statusCode = error.response?.statusCode;
    final serverMessage = _extractServerMessage(error.response?.data);

    return AppException(
      serverMessage ?? _networkMessage(error.type),
      statusCode: statusCode,
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
        'The request timed out. Check the backend and try again.',
      DioExceptionType.connectionError =>
        'Unable to connect to the P-TRADER AI backend.',
      DioExceptionType.badCertificate =>
        'The backend security certificate could not be verified.',
      DioExceptionType.cancel => 'The exchange request was cancelled.',
      _ => 'The exchange request failed. Check the connection and try again.',
    };
  }
}
