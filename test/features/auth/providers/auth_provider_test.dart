import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/features/auth/data/auth_user.dart';
import 'package:p_trader_ai/features/auth/domain/auth_repository.dart';
import 'package:p_trader_ai/features/auth/providers/auth_provider.dart';

void main() {
  group('AuthNotifier', () {
    test('registers and authenticates a new user', () async {
      final repository = _FakeAuthRepository();

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      final registered = await container
          .read(authProvider.notifier)
          .register(
            fullName: 'Test User',
            email: 'user@example.com',
            password: 'Password123',
            rememberMe: true,
          );

      final state = container.read(authProvider);

      expect(registered, isTrue);
      expect(repository.registerCalls, 1);
      expect(state.isAuthenticated, isTrue);
      expect(state.user?.email, 'user@example.com');
    });

    test('restores an authenticated session', () async {
      final repository = _FakeAuthRepository(restoredUser: _testUser);

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      final restored = await container
          .read(authProvider.notifier)
          .restoreSession();

      final state = container.read(authProvider);

      expect(restored, isTrue);
      expect(state.isAuthenticated, isTrue);
      expect(state.user?.id, 7);
    });

    test('stays unauthenticated without a saved session', () async {
      final container = ProviderContainer(
        overrides: [
          authRepositoryProvider.overrideWithValue(_FakeAuthRepository()),
        ],
      );
      addTearDown(container.dispose);

      final restored = await container
          .read(authProvider.notifier)
          .restoreSession();

      expect(restored, isFalse);
      expect(container.read(authProvider).isAuthenticated, isFalse);
    });

    test('logout clears authenticated state', () async {
      final repository = _FakeAuthRepository(restoredUser: _testUser);

      final container = ProviderContainer(
        overrides: [authRepositoryProvider.overrideWithValue(repository)],
      );
      addTearDown(container.dispose);

      await container.read(authProvider.notifier).restoreSession();

      final loggedOut = await container.read(authProvider.notifier).logout();

      expect(loggedOut, isTrue);
      expect(repository.logoutCalls, 1);
      expect(container.read(authProvider).isAuthenticated, isFalse);
    });
  });
}

class _FakeAuthRepository implements AuthRepository {
  _FakeAuthRepository({this.restoredUser});

  final AuthUser? restoredUser;
  int logoutCalls = 0;
  int registerCalls = 0;

  @override
  Future<AuthUser> register({
    required String fullName,
    required String email,
    required String password,
    required bool rememberMe,
  }) async {
    registerCalls += 1;
    return _testUser;
  }

  @override
  Future<AuthUser> login({
    required String email,
    required String password,
    required bool rememberMe,
  }) async {
    return _testUser;
  }

  @override
  Future<void> logout() async {
    logoutCalls += 1;
  }

  @override
  Future<AuthUser?> restoreSession() async {
    return restoredUser;
  }
}

final AuthUser _testUser = AuthUser(
  id: 7,
  fullName: 'Test User',
  email: 'user@example.com',
  isActive: true,
  createdAt: DateTime.utc(2026, 7, 31),
);
