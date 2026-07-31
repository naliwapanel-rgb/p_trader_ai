import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/config/api_config.dart';

void main() {
  group('ApiConfig', () {
    test('keeps CoinGecko and backend URLs separate', () {
      expect(ApiConfig.coinGeckoBaseUrl, 'https://api.coingecko.com/api/v3');

      expect(ApiConfig.backendBaseUrl, isNot(ApiConfig.coinGeckoBaseUrl));
    });

    test('uses a valid backend API URI', () {
      final uri = Uri.parse(ApiConfig.backendBaseUrl);

      expect(uri.hasScheme, isTrue);
      expect(uri.scheme, 'https');
      expect(uri.path, endsWith('/api/v1'));
    });

    test('defines finite network timeouts', () {
      expect(ApiConfig.connectTimeout, const Duration(seconds: 15));
      expect(ApiConfig.receiveTimeout, const Duration(seconds: 15));
      expect(ApiConfig.sendTimeout, const Duration(seconds: 15));
    });
  });
}
