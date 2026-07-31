import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/auth_remote_data_source.dart';
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
      await ref
          .read(authRepositoryProvider)
          .login(email: email, password: password, rememberMe: rememberMe);

      state = const AuthState.authenticated();
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

  Future<void> logout() async {
    await ref.read(authRepositoryProvider).logout();
    state = const AuthState.unauthenticated();
  }

  void clearError() {
    if (state.errorMessage != null) {
      state = const AuthState.unauthenticated();
    }
  }
}
