import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/auth_remote_data_source.dart';
import '../data/auth_user.dart';
import '../data/auth_repository_impl.dart';
import '../domain/auth_repository.dart';
import 'auth_state.dart';

final authRemoteDataSourceProvider = Provider<AuthRemoteDataSource>((ref) {
  return DioAuthRemoteDataSource(ref.watch(backendDioClientProvider));
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepositoryImpl(
    remoteDataSource: ref.watch(authRemoteDataSourceProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  );
});

final authProvider = NotifierProvider<AuthNotifier, AuthState>(
  AuthNotifier.new,
);

class AuthNotifier extends Notifier<AuthState> {
  @override
  AuthState build() {
    return const AuthState.unauthenticated();
  }

  Future<bool> register({
    required String fullName,
    required String email,
    required String password,
    required bool rememberMe,
  }) async {
    if (state.isLoading) {
      return false;
    }

    state = const AuthState.loading();

    try {
      final user = await ref
          .read(authRepositoryProvider)
          .register(
            fullName: fullName,
            email: email,
            password: password,
            rememberMe: rememberMe,
          );

      state = AuthState.authenticated(user);
      return true;
    } on AppException catch (error) {
      state = AuthState.failure(error.message);
      return false;
    } catch (_) {
      state = const AuthState.failure(
        'Registration failed unexpectedly. Please try again.',
      );
      return false;
    }
  }

  Future<bool> login({
    required String email,
    required String password,
    required bool rememberMe,
  }) async {
    if (state.isLoading) {
      return false;
    }

    state = const AuthState.loading();

    try {
      final user = await ref
          .read(authRepositoryProvider)
          .login(email: email, password: password, rememberMe: rememberMe);

      state = AuthState.authenticated(user);
      return true;
    } on AppException catch (error) {
      state = AuthState.failure(error.message);
      return false;
    } catch (_) {
      state = const AuthState.failure(
        'Login failed unexpectedly. Please try again.',
      );
      return false;
    }
  }

  Future<bool> restoreSession() async {
    if (state.isLoading) {
      return false;
    }

    state = const AuthState.loading();

    try {
      final user = await ref.read(authRepositoryProvider).restoreSession();

      if (user == null) {
        state = const AuthState.unauthenticated();
        return false;
      }

      state = AuthState.authenticated(user);
      return true;
    } on AppException catch (error) {
      state = AuthState.failure(error.message);
      return false;
    } catch (_) {
      state = const AuthState.failure('Unable to restore the saved session.');
      return false;
    }
  }

  Future<AuthUser> updateProfile({
    required String fullName,
    required String email,
  }) async {
    _requireAuthenticatedUser();

    final updatedUser = await ref
        .read(authRepositoryProvider)
        .updateProfile(fullName: fullName, email: email);

    state = AuthState.authenticated(updatedUser);

    return updatedUser;
  }

  Future<void> updatePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    _requireAuthenticatedUser();

    await ref
        .read(authRepositoryProvider)
        .updatePassword(
          currentPassword: currentPassword,
          newPassword: newPassword,
        );
  }

  Future<void> deactivateAccount() async {
    _requireAuthenticatedUser();

    await ref.read(authRepositoryProvider).deactivateAccount();

    state = const AuthState.unauthenticated();
  }

  AuthUser _requireAuthenticatedUser() {
    final user = state.user;

    if (!state.isAuthenticated || user == null) {
      throw const AppException(
        'You must be logged in to manage this account.',
        statusCode: 401,
      );
    }

    return user;
  }

  Future<bool> logout() async {
    if (state.isLoading) {
      return false;
    }

    state = const AuthState.loading();

    try {
      await ref.read(authRepositoryProvider).logout();
      state = const AuthState.unauthenticated();
      return true;
    } catch (_) {
      state = const AuthState.failure('Logout failed. Please try again.');
      return false;
    }
  }

  void clearError() {
    if (state.errorMessage != null) {
      state = const AuthState.unauthenticated();
    }
  }

  void expireSession({
    String message = 'Your session has expired. Please log in again.',
  }) {
    state = AuthState.failure(message);
  }
}
