import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/auth/data/auth_remote_data_source.dart';
import 'package:p_trader_ai/features/auth/data/auth_repository_impl.dart';
import 'package:p_trader_ai/features/auth/data/auth_token.dart';
import 'package:p_trader_ai/features/auth/data/auth_user.dart';

void main() {
  group('AuthRepositoryImpl', () {
    test('registration stores the token and returns user', () async {
      final storage = _MemoryTokenStorage();
      final remote = _FakeAuthRemoteDataSource();

      final repository = AuthRepositoryImpl(
        remoteDataSource: remote,
        tokenStorage: storage,
      );

      final user = await repository.register(
        fullName: 'Test User',
        email: 'user@example.com',
        password: 'Password123',
        rememberMe: true,
      );

      expect(remote.registerCalls, 1);
      expect(storage.token, 'registration-token');
      expect(storage.persist, isTrue);
      expect(user.id, 7);
    });

    test('login stores a persistent token and returns user', () async {
      final storage = _MemoryTokenStorage();

      final repository = AuthRepositoryImpl(
        remoteDataSource: _FakeAuthRemoteDataSource(),
        tokenStorage: storage,
      );

      final user = await repository.login(
        email: 'user@example.com',
        password: 'Password123',
        rememberMe: true,
      );

      expect(storage.token, 'test-token');
      expect(storage.persist, isTrue);
      expect(user.id, 7);
    });

    test('login supports session-only storage', () async {
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

      expect(storage.persist, isFalse);
    });

    test('restore returns null when no token exists', () async {
      final remote = _FakeAuthRemoteDataSource();

      final repository = AuthRepositoryImpl(
        remoteDataSource: remote,
        tokenStorage: _MemoryTokenStorage(),
      );

      final user = await repository.restoreSession();

      expect(user, isNull);
      expect(remote.profileRequests, 0);
    });

    test('restore validates and returns a stored session', () async {
      final storage = _MemoryTokenStorage()..token = 'existing-token';

      final repository = AuthRepositoryImpl(
        remoteDataSource: _FakeAuthRemoteDataSource(),
        tokenStorage: storage,
      );

      final user = await repository.restoreSession();

      expect(user?.id, 7);
    });

    test('restore deletes an invalid stored token', () async {
      final storage = _MemoryTokenStorage()..token = 'expired-token';

      final repository = AuthRepositoryImpl(
        remoteDataSource: _FakeAuthRemoteDataSource(
          profileError: const AppException(
            'Invalid or expired token',
            statusCode: 401,
          ),
        ),
        tokenStorage: storage,
      );

      final user = await repository.restoreSession();

      expect(user, isNull);
      expect(storage.token, isNull);
      expect(storage.deleteCalls, 1);
    });

    test('restore preserves token on temporary failures', () async {
      final storage = _MemoryTokenStorage()..token = 'existing-token';

      final repository = AuthRepositoryImpl(
        remoteDataSource: _FakeAuthRemoteDataSource(
          profileError: const AppException(
            'Service unavailable',
            statusCode: 503,
          ),
        ),
        tokenStorage: storage,
      );

      await expectLater(
        repository.restoreSession(),
        throwsA(isA<AppException>()),
      );

      expect(storage.token, 'existing-token');
    });

    test('updates profile through the backend', () async {
      final remote = _FakeAuthRemoteDataSource();

      final repository = AuthRepositoryImpl(
        remoteDataSource: remote,
        tokenStorage: _MemoryTokenStorage(),
      );

      final user = await repository.updateProfile(
        fullName: 'Updated User',
        email: 'updated@example.com',
      );

      expect(remote.updateProfileCalls, 1);
      expect(remote.updatedFullName, 'Updated User');
      expect(remote.updatedEmail, 'updated@example.com');
      expect(user.fullName, 'Updated User');
      expect(user.email, 'updated@example.com');
    });

    test('updates password through the backend', () async {
      final remote = _FakeAuthRemoteDataSource();

      final repository = AuthRepositoryImpl(
        remoteDataSource: remote,
        tokenStorage: _MemoryTokenStorage(),
      );

      await repository.updatePassword(
        currentPassword: 'Password123',
        newPassword: 'NewPassword456',
      );

      expect(remote.updatePasswordCalls, 1);
      expect(remote.currentPassword, 'Password123');
      expect(remote.newPassword, 'NewPassword456');
    });

    test('deactivation clears the local token', () async {
      final remote = _FakeAuthRemoteDataSource();
      final storage = _MemoryTokenStorage()..token = 'existing-token';

      final repository = AuthRepositoryImpl(
        remoteDataSource: remote,
        tokenStorage: storage,
      );

      await repository.deactivateAccount();

      expect(remote.deactivateCalls, 1);
      expect(storage.token, isNull);
      expect(storage.deleteCalls, 1);
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
  _FakeAuthRemoteDataSource({this.profileError});

  final AppException? profileError;
  int profileRequests = 0;
  int registerCalls = 0;
  int updateProfileCalls = 0;
  int updatePasswordCalls = 0;
  int deactivateCalls = 0;
  String? updatedFullName;
  String? updatedEmail;
  String? currentPassword;
  String? newPassword;

  @override
  Future<AuthToken> register({
    required String fullName,
    required String email,
    required String password,
  }) async {
    registerCalls += 1;

    return const AuthToken(
      accessToken: 'registration-token',
      tokenType: 'bearer',
    );
  }

  @override
  Future<AuthToken> login({
    required String email,
    required String password,
  }) async {
    return const AuthToken(accessToken: 'test-token', tokenType: 'bearer');
  }

  @override
  Future<AuthUser> updateProfile({
    required String fullName,
    required String email,
  }) async {
    updateProfileCalls += 1;
    updatedFullName = fullName;
    updatedEmail = email;

    return AuthUser(
      id: 7,
      fullName: fullName,
      email: email,
      isActive: true,
      createdAt: DateTime.utc(2026, 7, 31),
    );
  }

  @override
  Future<void> updatePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    updatePasswordCalls += 1;
    this.currentPassword = currentPassword;
    this.newPassword = newPassword;
  }

  @override
  Future<void> deactivateAccount() async {
    deactivateCalls += 1;
  }

  @override
  Future<AuthUser> getCurrentUser() async {
    profileRequests += 1;

    final error = profileError;

    if (error != null) {
      throw error;
    }

    return _testUser;
  }
}

class _MemoryTokenStorage implements TokenStorage {
  String? token;
  bool? persist;
  int deleteCalls = 0;

  @override
  Future<void> deleteAccessToken() async {
    deleteCalls += 1;
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

final AuthUser _testUser = AuthUser(
  id: 7,
  fullName: 'Test User',
  email: 'user@example.com',
  isActive: true,
  createdAt: DateTime.fromMillisecondsSinceEpoch(0, isUtc: true),
);
