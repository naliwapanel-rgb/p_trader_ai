import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class TokenStorage {
  Future<String?> readAccessToken();

  Future<void> writeAccessToken(String token);

  Future<void> deleteAccessToken();
}

class SecureTokenStorage implements TokenStorage {
  const SecureTokenStorage(this._storage);

  static const String accessTokenKey = 'p_trader_access_token';

  final FlutterSecureStorage _storage;

  @override
  Future<String?> readAccessToken() {
    return _storage.read(key: accessTokenKey);
  }

  @override
  Future<void> writeAccessToken(String token) {
    return _storage.write(key: accessTokenKey, value: token);
  }

  @override
  Future<void> deleteAccessToken() {
    return _storage.delete(key: accessTokenKey);
  }
}
