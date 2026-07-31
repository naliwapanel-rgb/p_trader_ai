class ApiConfig {
  const ApiConfig._();

  static const String coinGeckoBaseUrl = 'https://api.coingecko.com/api/v3';

  /// Override this value at runtime with:
  ///
  /// --dart-define=P_TRADER_API_BASE_URL=https://example.com/api/v1
  ///
  /// Android Emulator example:
  ///
  /// --dart-define=P_TRADER_API_BASE_URL=https://10.0.2.2/api/v1
  static const String backendBaseUrl = String.fromEnvironment(
    'P_TRADER_API_BASE_URL',
    defaultValue: 'https://127.0.0.1/api/v1',
  );

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);
  static const Duration sendTimeout = Duration(seconds: 15);
}
