import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/auth/token_storage.dart';

void main() {
  group('SecureTokenStorage', () {
    test('reads, normalizes, and caches a persisted token', () async {
      final secureStore = _FakeSecureTokenStore(value: '  persisted-token  ');

      final tokenStorage = SecureTokenStorage.withStore(secureStore);

      expect(await tokenStorage.readAccessToken(), 'persisted-token');

      secureStore.readError = _keyringLockedError();

      expect(await tokenStorage.readAccessToken(), 'persisted-token');

      expect(secureStore.readCount, 1);
    });

    test('returns null when the keyring is locked', () async {
      final secureStore = _FakeSecureTokenStore(
        readError: _keyringLockedError(),
      );

      final tokenStorage = SecureTokenStorage.withStore(secureStore);

      expect(await tokenStorage.readAccessToken(), isNull);

      expect(await tokenStorage.readAccessToken(), isNull);

      expect(secureStore.readCount, 1);
    });

    test(
      'keeps a persistent login in memory when secure writing fails',
      () async {
        final secureStore = _FakeSecureTokenStore(
          writeError: _keyringLockedError(),
        );

        final tokenStorage = SecureTokenStorage.withStore(secureStore);

        await tokenStorage.writeAccessToken('session-token', persist: true);

        expect(await tokenStorage.readAccessToken(), 'session-token');

        expect(secureStore.writeCount, 1);
        expect(secureStore.readCount, 0);
      },
    );

    test('keeps non-persistent authentication in memory', () async {
      final secureStore = _FakeSecureTokenStore(value: 'old-token');

      final tokenStorage = SecureTokenStorage.withStore(secureStore);

      await tokenStorage.writeAccessToken('temporary-token', persist: false);

      expect(await tokenStorage.readAccessToken(), 'temporary-token');

      expect(secureStore.value, isNull);
      expect(secureStore.deleteCount, 1);
    });

    test('clears the memory token even when keyring deletion fails', () async {
      final secureStore = _FakeSecureTokenStore();

      final tokenStorage = SecureTokenStorage.withStore(secureStore);

      await tokenStorage.writeAccessToken('temporary-token', persist: false);

      secureStore.deleteError = _keyringLockedError();

      await tokenStorage.deleteAccessToken();

      expect(await tokenStorage.readAccessToken(), isNull);

      expect(secureStore.deleteCount, 2);
    });
  });
}

PlatformException _keyringLockedError() {
  return PlatformException(code: 'KeyringLocked', message: 'KeyringLocked');
}

final class _FakeSecureTokenStore implements SecureTokenStore {
  _FakeSecureTokenStore({this.value, this.readError, this.writeError});

  String? value;
  Object? readError;
  Object? writeError;
  Object? deleteError;

  int readCount = 0;
  int writeCount = 0;
  int deleteCount = 0;

  @override
  Future<String?> read({required String key}) async {
    readCount += 1;

    final error = readError;

    if (error != null) {
      throw error;
    }

    return value;
  }

  @override
  Future<void> write({required String key, required String value}) async {
    writeCount += 1;

    final error = writeError;

    if (error != null) {
      throw error;
    }

    this.value = value;
  }

  @override
  Future<void> delete({required String key}) async {
    deleteCount += 1;

    final error = deleteError;

    if (error != null) {
      throw error;
    }

    value = null;
  }
}
