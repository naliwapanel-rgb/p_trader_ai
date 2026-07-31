import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/features/auth/data/auth_remote_data_source.dart';
import 'package:p_trader_ai/features/auth/data/auth_repository_impl.dart';
import 'package:p_trader_ai/features/auth/data/auth_token.dart';

void main() {
  group('AuthRepositoryImpl', () {
    test('stores a persistent token when remember me is enabled', () async {
      final storage = _MemoryTokenStorage();

      final repository = AuthRepositoryImpl(
        remoteDataSource: _FakeAuthRemoteDataSource(),
        tokenStorage: storage,
      );

      await repository.login(
        email: 'user@example.com',
        password: 'Password123',
        rememberMe: true,
      );

      expect(storage.token, 'test-token');
      expect(storage.persist, isTrue);
    });

    test('stores a session-only token when remember me is disabled', () async {
      final storage = _MemoryTokenStorage();

      final repository = AuthRepositoryImpl(
        remoteDataSource: _FakeAuthRemoteDataSource(),
        tokenStorage: storage,
      );

      await repository.login(
        email: 'user@example.com',
        password: 'Password123',
        rememberMe: false,
      );

      expect(storage.token, 'test-token');
      expect(storage.persist, isFalse);
    });

    test('logout deletes the token', () async {
      final storage = _MemoryTokenStorage()..token = 'existing-token';

      final repository = AuthRepositoryImpl(
        remoteDataSource: _FakeAuthRemoteDataSource(),
        tokenStorage: storage,
      );

      await repository.logout();

      expect(storage.token, isNull);
    });
  });
}

class _FakeAuthRemoteDataSource implements AuthRemoteDataSource {
  @override
  Future<AuthToken> login({
    required String email,
    required String password,
  }) async {
    return const AuthToken(accessToken: 'test-token', tokenType: 'bearer');
  }
}

class _MemoryTokenStorage implements TokenStorage {
  String? token;
  bool? persist;

  @override
  Future<void> deleteAccessToken() async {
    token = null;
  }

  @override
  Future<String?> readAccessToken() async {
    return token;
  }

  @override
  Future<void> writeAccessToken(String token, {bool persist = true}) async {
    this.token = token;
    this.persist = persist;
  }
}
