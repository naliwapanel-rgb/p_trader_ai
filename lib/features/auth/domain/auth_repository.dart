abstract interface class AuthRepository {
  Future<void> login({
    required String email,
    required String password,
    required bool rememberMe,
  });

  Future<void> logout();

  Future<bool> hasStoredSession();
}
