import 'package:dio/dio.dart';

import '../config/api_config.dart';
import '../logging/app_logger.dart';

class DioClient {
  late final Dio dio;

  DioClient() {
    dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.coinGeckoBaseUrl,
        connectTimeout: ApiConfig.connectTimeout,
        receiveTimeout: ApiConfig.receiveTimeout,
        headers: {'Accept': 'application/json'},
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          AppLogger.instance.i("REQUEST => ${options.method} ${options.uri}");
          handler.next(options);
        },
        onResponse: (response, handler) {
          AppLogger.instance.i("RESPONSE => ${response.statusCode}");
          handler.next(response);
        },
        onError: (error, handler) {
          AppLogger.instance.e("ERROR => ${error.message}", error: error);
          handler.next(error);
        },
      ),
    );
  }
}
