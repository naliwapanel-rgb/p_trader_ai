import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/auth/data/auth_token.dart';

void main() {
  group('AuthToken', () {
    test('parses a valid token response', () {
      final token = AuthToken.fromJson(const <String, dynamic>{
        'access_token': 'jwt-token',
        'token_type': 'bearer',
      });

      expect(token.accessToken, 'jwt-token');
      expect(token.tokenType, 'bearer');
    });

    test('uses bearer when token_type is omitted', () {
      final token = AuthToken.fromJson(const <String, dynamic>{
        'access_token': 'jwt-token',
      });

      expect(token.tokenType, 'bearer');
    });

    test('rejects a response without an access token', () {
      expect(
        () => AuthToken.fromJson(const <String, dynamic>{}),
        throwsFormatException,
      );
    });
  });
}
