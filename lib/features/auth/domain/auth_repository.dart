import '../data/auth_user.dart';

abstract interface class AuthRepository {
  Future<AuthUser> register({
    required String fullName,
    required String email,
    required String password,
    required bool rememberMe,
  });

  Future<AuthUser> login({
    required String email,
    required String password,
    required bool rememberMe,
  });

  Future<AuthUser?> restoreSession();

  Future<AuthUser> updateProfile({
    required String fullName,
    required String email,
  });

  Future<void> updatePassword({
    required String currentPassword,
    required String newPassword,
  });

  Future<void> deactivateAccount();

  Future<void> logout();
}
