import 'package:dio/dio.dart';

import '../config/api_config.dart';
import '../logging/app_logger.dart';

class DioClient {
  DioClient({Dio? dio})
    : dio =
          dio ??
          Dio(
            BaseOptions(
              baseUrl: ApiConfig.coinGeckoBaseUrl,

              // CoinGecko occasionally spends 10-16 seconds
              // resolving or negotiating a connection. The app
              // already has last-known-good cache fallback, so it
              // should not leave the interface waiting that long.
              connectTimeout: const Duration(seconds: 8),
              receiveTimeout: const Duration(seconds: 10),
              sendTimeout: const Duration(seconds: 8),

              headers: const <String, Object>{
                Headers.acceptHeader: Headers.jsonContentType,
              },
            ),
          ) {
    this.dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          AppLogger.instance.i(
            'REQUEST => '
            '${options.method} ${options.uri}',
          );

          handler.next(options);
        },
        onResponse: (response, handler) {
          AppLogger.instance.i('RESPONSE => ${response.statusCode}');

          handler.next(response);
        },
        onError: (error, handler) {
          AppLogger.instance.e(
            'MARKET ERROR => '
            '${error.response?.statusCode} '
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
