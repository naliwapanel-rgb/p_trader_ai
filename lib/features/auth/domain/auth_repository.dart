import '../data/auth_user.dart';

abstract interface class AuthRepository {
  Future<AuthUser> login({
    required String email,
    required String password,
    required bool rememberMe,
  });

  Future<AuthUser?> restoreSession();

  Future<void> logout();
}
