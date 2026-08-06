class ApiConfig {
  const ApiConfig._();

  static const String coinGeckoBaseUrl = 'https://api.coingecko.com/api/v3';

  /// Configure the backend at build time with:
  ///
  /// --dart-define=P_TRADER_API_BASE_URL=https://example.com/api/v1
  ///
  /// Android Emulator example:
  ///
  /// --dart-define=P_TRADER_API_BASE_URL=https://10.0.2.2/api/v1
  static const String _configuredBackendBaseUrl = String.fromEnvironment(
    'P_TRADER_API_BASE_URL',
  );

  static bool get hasBackendBaseUrl =>
      _configuredBackendBaseUrl.trim().isNotEmpty;

  static String get backendBaseUrl =>
      validateBackendBaseUrl(_configuredBackendBaseUrl);

  static String validateBackendBaseUrl(String value) {
    final normalized = value.trim();

    if (normalized.isEmpty) {
      throw StateError(
        'P_TRADER_API_BASE_URL is required. Build the app with '
        '--dart-define=P_TRADER_API_BASE_URL=https://example.com/api/v1.',
      );
    }

    final uri = Uri.tryParse(normalized);
    final isValid =
        uri != null &&
        uri.scheme == 'https' &&
        uri.host.isNotEmpty &&
        uri.path.endsWith('/api/v1') &&
        uri.query.isEmpty &&
        uri.fragment.isEmpty;

    if (!isValid) {
      throw StateError(
        'P_TRADER_API_BASE_URL must be an HTTPS URL ending in /api/v1 '
        'without a query string or fragment.',
      );
    }

    return normalized;
  }

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 15);
  static const Duration sendTimeout = Duration(seconds: 15);
}
