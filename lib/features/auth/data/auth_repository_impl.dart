import '../../../core/auth/token_storage.dart';
import '../domain/auth_repository.dart';
import 'auth_remote_data_source.dart';

class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl({
    required AuthRemoteDataSource remoteDataSource,
    required TokenStorage tokenStorage,
  }) : _remoteDataSource = remoteDataSource,
       _tokenStorage = tokenStorage;

  final AuthRemoteDataSource _remoteDataSource;
  final TokenStorage _tokenStorage;

  @override
  Future<void> login({
    required String email,
    required String password,
    required bool rememberMe,
  }) async {
    final token = await _remoteDataSource.login(
      email: email,
      password: password,
    );

    await _tokenStorage.writeAccessToken(
      token.accessToken,
      persist: rememberMe,
    );
  }

  @override
  Future<void> logout() {
    return _tokenStorage.deleteAccessToken();
  }

  @override
  Future<bool> hasStoredSession() async {
    final token = await _tokenStorage.readAccessToken();
    return token != null && token.trim().isNotEmpty;
  }
}
