import 'package:dio/dio.dart';

import '../auth/token_storage.dart';
import '../config/api_config.dart';
import '../logging/app_logger.dart';

class BackendDioClient {
  static const String authorizationHeader = 'Authorization';

  BackendDioClient({required TokenStorage tokenStorage, Dio? dio})
    : dio =
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
          final token = await tokenStorage.readAccessToken();

          final isAuthenticationRequest = options.path.startsWith('/auth/');

          if (!isAuthenticationRequest &&
              token != null &&
              token.trim().isNotEmpty) {
            options.headers[authorizationHeader] = 'Bearer ${token.trim()}';
          }

          AppLogger.instance.i(
            'BACKEND REQUEST => ${options.method} ${options.uri}',
          );

          handler.next(options);
        },
        onResponse: (response, handler) {
          AppLogger.instance.i(
            'BACKEND RESPONSE => ${response.statusCode} '
            '${response.requestOptions.uri}',
          );

          handler.next(response);
        },
        onError: (error, handler) {
          AppLogger.instance.e(
            'BACKEND ERROR => ${error.response?.statusCode} '
            '${error.requestOptions.method} '
            '${error.requestOptions.uri}',
          );

          handler.next(error);
        },
      ),
    );
  }

  final Dio dio;
}
