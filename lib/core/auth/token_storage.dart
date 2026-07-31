import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class TokenStorage {
  Future<String?> readAccessToken();

  Future<void> writeAccessToken(String token, {bool persist = true});

  Future<void> deleteAccessToken();
}

class SecureTokenStorage implements TokenStorage {
  SecureTokenStorage(this._storage);

  static const String accessTokenKey = 'p_trader_access_token';

  final FlutterSecureStorage _storage;

  String? _sessionToken;

  @override
  Future<String?> readAccessToken() async {
    final sessionToken = _sessionToken;

    if (sessionToken != null && sessionToken.isNotEmpty) {
      return sessionToken;
    }

    return _storage.read(key: accessTokenKey);
  }

  @override
  Future<void> writeAccessToken(String token, {bool persist = true}) async {
    final normalizedToken = token.trim();

    if (normalizedToken.isEmpty) {
      throw ArgumentError.value(
        token,
        'token',
        'Access token cannot be empty.',
      );
    }

    _sessionToken = normalizedToken;

    if (persist) {
      await _storage.write(key: accessTokenKey, value: normalizedToken);
      return;
    }

    await _storage.delete(key: accessTokenKey);
  }

  @override
  Future<void> deleteAccessToken() async {
    _sessionToken = null;
    await _storage.delete(key: accessTokenKey);
  }
}
