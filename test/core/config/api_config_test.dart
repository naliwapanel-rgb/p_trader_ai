import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/config/api_config.dart';

void main() {
  group('ApiConfig', () {
    test('keeps the CoinGecko URL independent from backend configuration', () {
      expect(ApiConfig.coinGeckoBaseUrl, 'https://api.coingecko.com/api/v3');
    });

    test('fails closed when the backend build definition is missing', () {
      if (ApiConfig.hasBackendBaseUrl) {
        expect(ApiConfig.backendBaseUrl, isNotEmpty);
        return;
      }

      expect(
        () => ApiConfig.backendBaseUrl,
        throwsA(
          isA<StateError>().having(
            (error) => error.message,
            'message',
            contains('P_TRADER_API_BASE_URL is required'),
          ),
        ),
      );
    });

    test('accepts a valid HTTPS backend API URI', () {
      expect(
        ApiConfig.validateBackendBaseUrl('  https://api.example.com/api/v1  '),
        'https://api.example.com/api/v1',
      );
    });

    test('rejects unsafe or malformed backend API URIs', () {
      const invalidValues = <String>[
        '',
        'http://api.example.com/api/v1',
        'https://api.example.com',
        'https:///api/v1',
        'https://api.example.com/api/v1?debug=true',
        'https://api.example.com/api/v1#debug',
      ];

      for (final value in invalidValues) {
        expect(
          () => ApiConfig.validateBackendBaseUrl(value),
          throwsA(isA<StateError>()),
          reason: 'Expected "$value" to be rejected.',
        );
      }
    });

    test('validates the configured backend API URI when supplied', () {
      if (!ApiConfig.hasBackendBaseUrl) {
        return;
      }

      final uri = Uri.parse(ApiConfig.backendBaseUrl);

      expect(uri.scheme, 'https');
      expect(uri.host, isNotEmpty);
      expect(uri.path, endsWith('/api/v1'));
      expect(uri.query, isEmpty);
      expect(uri.fragment, isEmpty);
    });

    test('defines finite network timeouts', () {
      expect(ApiConfig.connectTimeout, const Duration(seconds: 15));
      expect(ApiConfig.receiveTimeout, const Duration(seconds: 15));
      expect(ApiConfig.sendTimeout, const Duration(seconds: 15));
    });
  });
}
