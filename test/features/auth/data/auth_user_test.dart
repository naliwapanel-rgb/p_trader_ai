import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/auth/data/auth_user.dart';

void main() {
  group('AuthUser', () {
    test('parses a valid backend user', () {
      final user = AuthUser.fromJson(const <String, dynamic>{
        'id': 7,
        'full_name': 'Test User',
        'email': 'user@example.com',
        'is_active': true,
        'created_at': '2026-07-31T10:30:00Z',
      });

      expect(user.id, 7);
      expect(user.fullName, 'Test User');
      expect(user.email, 'user@example.com');
      expect(user.isActive, isTrue);
      expect(user.createdAt.isUtc, isTrue);
    });

    test('rejects invalid user data', () {
      expect(
        () => AuthUser.fromJson(const <String, dynamic>{
          'id': 0,
          'full_name': '',
          'email': '',
          'is_active': true,
          'created_at': 'invalid',
        }),
        throwsFormatException,
      );
    });
  });
}
