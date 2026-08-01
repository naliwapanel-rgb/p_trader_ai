import '../../../core/auth/token_storage.dart';
import '../../../core/errors/app_exception.dart';
import '../domain/auth_repository.dart';
import 'auth_remote_data_source.dart';
import 'auth_user.dart';

class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl({
    required AuthRemoteDataSource remoteDataSource,
    required TokenStorage tokenStorage,
  }) : _remoteDataSource = remoteDataSource,
       _tokenStorage = tokenStorage;

  final AuthRemoteDataSource _remoteDataSource;
  final TokenStorage _tokenStorage;

  @override
  Future<AuthUser> register({
    required String fullName,
    required String email,
    required String password,
    required bool rememberMe,
  }) async {
    final token = await _remoteDataSource.register(
      fullName: fullName,
      email: email,
      password: password,
    );

    return _completeAuthentication(
      accessToken: token.accessToken,
      persist: rememberMe,
    );
  }

  @override
  Future<AuthUser> login({
    required String email,
    required String password,
    required bool rememberMe,
  }) async {
    final token = await _remoteDataSource.login(
      email: email,
      password: password,
    );

    return _completeAuthentication(
      accessToken: token.accessToken,
      persist: rememberMe,
    );
  }

  Future<AuthUser> _completeAuthentication({
    required String accessToken,
    required bool persist,
  }) async {
    await _tokenStorage.writeAccessToken(accessToken, persist: persist);

    try {
      return await _remoteDataSource.getCurrentUser();
    } catch (_) {
      await _tokenStorage.deleteAccessToken();
      rethrow;
    }
  }

  @override
  Future<AuthUser?> restoreSession() async {
    final token = await _tokenStorage.readAccessToken();

    if (token == null || token.trim().isEmpty) {
      return null;
    }

    try {
      return await _remoteDataSource.getCurrentUser();
    } on AppException catch (error) {
      if (error.statusCode == 401 || error.statusCode == 403) {
        await _tokenStorage.deleteAccessToken();
        return null;
      }

      rethrow;
    }
  }

  @override
  Future<AuthUser> updateProfile({
    required String fullName,
    required String email,
  }) {
    return _remoteDataSource.updateProfile(fullName: fullName, email: email);
  }

  @override
  Future<void> updatePassword({
    required String currentPassword,
    required String newPassword,
  }) {
    return _remoteDataSource.updatePassword(
      currentPassword: currentPassword,
      newPassword: newPassword,
    );
  }

  @override
  Future<void> deactivateAccount() async {
    await _remoteDataSource.deactivateAccount();
    await _tokenStorage.deleteAccessToken();
  }

  @override
  Future<void> logout() {
    return _tokenStorage.deleteAccessToken();
  }
}
