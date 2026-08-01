import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class TokenStorage {
  Future<String?> readAccessToken();

  Future<void> writeAccessToken(String token, {required bool persist});

  Future<void> deleteAccessToken();
}

abstract interface class SecureTokenStore {
  Future<String?> read({required String key});

  Future<void> write({required String key, required String value});

  Future<void> delete({required String key});
}

final class FlutterSecureTokenStore implements SecureTokenStore {
  const FlutterSecureTokenStore(this._storage);

  final FlutterSecureStorage _storage;

  @override
  Future<String?> read({required String key}) {
    return _storage.read(key: key);
  }

  @override
  Future<void> write({required String key, required String value}) {
    return _storage.write(key: key, value: value);
  }

  @override
  Future<void> delete({required String key}) {
    return _storage.delete(key: key);
  }
}

final class SecureTokenStorage implements TokenStorage {
  SecureTokenStorage(FlutterSecureStorage storage)
    : this.withStore(FlutterSecureTokenStore(storage));

  SecureTokenStorage.withStore(SecureTokenStore storage) : _storage = storage;

  static const String accessTokenKey = 'p_trader_access_token';

  final SecureTokenStore _storage;

  String? _memoryAccessToken;
  bool _secureStorageAvailable = true;

  @override
  Future<String?> readAccessToken() async {
    final memoryToken = _normalizeToken(_memoryAccessToken);

    if (memoryToken != null) {
      return memoryToken;
    }

    if (!_secureStorageAvailable) {
      return null;
    }

    try {
      final persistedToken = _normalizeToken(
        await _storage.read(key: accessTokenKey),
      );

      _memoryAccessToken = persistedToken;

      return persistedToken;
    } on PlatformException {
      _secureStorageAvailable = false;
      return null;
    } on MissingPluginException {
      _secureStorageAvailable = false;
      return null;
    }
  }

  @override
  Future<void> writeAccessToken(String token, {required bool persist}) async {
    final normalizedToken = _normalizeToken(token);

    if (normalizedToken == null) {
      await deleteAccessToken();
      return;
    }

    // Keep authentication usable for the current application
    // process even when Linux secure storage is unavailable.
    _memoryAccessToken = normalizedToken;

    if (!persist) {
      await _deletePersistedToken();
      return;
    }

    if (!_secureStorageAvailable) {
      return;
    }

    try {
      await _storage.write(key: accessTokenKey, value: normalizedToken);
    } on PlatformException {
      _secureStorageAvailable = false;
    } on MissingPluginException {
      _secureStorageAvailable = false;
    }
  }

  @override
  Future<void> deleteAccessToken() async {
    _memoryAccessToken = null;

    await _deletePersistedToken();
  }

  Future<void> _deletePersistedToken() async {
    if (!_secureStorageAvailable) {
      return;
    }

    try {
      await _storage.delete(key: accessTokenKey);
    } on PlatformException {
      _secureStorageAvailable = false;
    } on MissingPluginException {
      _secureStorageAvailable = false;
    }
  }

  String? _normalizeToken(String? token) {
    final normalizedToken = token?.trim();

    if (normalizedToken == null || normalizedToken.isEmpty) {
      return null;
    }

    return normalizedToken;
  }
}
