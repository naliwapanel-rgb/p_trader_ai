import 'dart:async';

import 'package:dio/dio.dart';

import '../auth/token_storage.dart';
import '../config/api_config.dart';
import '../logging/app_logger.dart';

typedef UnauthorizedCallback = FutureOr<void> Function(String message);

class BackendDioClient {
  static const String authorizationHeader = 'Authorization';

  static const String _requestTokenKey = 'p_trader_request_access_token';

  BackendDioClient({
    required TokenStorage tokenStorage,
    UnauthorizedCallback? onUnauthorized,
    Dio? dio,
  }) : _tokenStorage = tokenStorage,
       _onUnauthorized = onUnauthorized,
       dio =
           dio ??
           Dio(
             BaseOptions(
               baseUrl: ApiConfig.backendBaseUrl,
               connectTimeout: ApiConfig.connectTimeout,
               receiveTimeout: ApiConfig.receiveTimeout,
               sendTimeout: ApiConfig.sendTimeout,
               headers: const <String, Object>{
                 Headers.acceptHeader: Headers.jsonContentType,
                 Headers.contentTypeHeader: Headers.jsonContentType,
               },
             ),
           ) {
    this.dio.interceptors.add(
      QueuedInterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStorage.readAccessToken();

          final isAuthenticationRequest = _isAuthenticationRequest(
            options.path,
          );

          if (!isAuthenticationRequest &&
              token != null &&
              token.trim().isNotEmpty) {
            final normalizedToken = token.trim();

            options.headers[authorizationHeader] = 'Bearer $normalizedToken';

            options.extra[_requestTokenKey] = normalizedToken;
          }

          AppLogger.instance.i(
            'BACKEND REQUEST => '
            '${options.method} ${options.uri}',
          );

          handler.next(options);
        },
        onResponse: (response, handler) {
          AppLogger.instance.i(
            'BACKEND RESPONSE => '
            '${response.statusCode} '
            '${response.requestOptions.uri}',
          );

          handler.next(response);
        },
        onError: (error, handler) async {
          AppLogger.instance.e(
            'BACKEND ERROR => '
            '${error.response?.statusCode} '
            '${error.requestOptions.method} '
            '${error.requestOptions.uri}',
          );

          await _handleUnauthorized(error);

          handler.next(error);
        },
      ),
    );
  }

  final TokenStorage _tokenStorage;
  final UnauthorizedCallback? _onUnauthorized;

  final Dio dio;

  Future<void> _handleUnauthorized(DioException error) async {
    if (error.response?.statusCode != 401) {
      return;
    }

    if (_isAuthenticationRequest(error.requestOptions.path)) {
      return;
    }

    final requestToken = error.requestOptions.extra[_requestTokenKey];

    if (requestToken is! String || requestToken.trim().isEmpty) {
      return;
    }

    final currentToken = await _tokenStorage.readAccessToken();

    // Do not invalidate a newer session because an old
    // request returned late with a 401 response.
    if (currentToken == null || currentToken.trim() != requestToken.trim()) {
      return;
    }

    await _tokenStorage.deleteAccessToken();

    final callback = _onUnauthorized;

    if (callback != null) {
      await callback(_extractUnauthorizedMessage(error.response?.data));
    }
  }

  bool _isAuthenticationRequest(String path) {
    return path.startsWith('/auth/') || path.contains('/auth/');
  }

  String _extractUnauthorizedMessage(Object? data) {
    if (data is Map) {
      final message = data['message'];

      if (message is String && message.trim().isNotEmpty) {
        return message.trim();
      }

      final detail = data['detail'];

      if (detail is String && detail.trim().isNotEmpty) {
        return detail.trim();
      }
    }

    return 'Your session has expired. '
        'Please log in again.';
  }
}
