import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../auth/session_expiry_provider.dart';
import '../auth/token_storage.dart';
import '../network/backend_dio_client.dart';

final flutterSecureStorageProvider = Provider<FlutterSecureStorage>((ref) {
  return const FlutterSecureStorage();
});

final tokenStorageProvider = Provider<TokenStorage>((ref) {
  final secureStorage = ref.watch(flutterSecureStorageProvider);

  return SecureTokenStorage(secureStorage);
});

final backendDioClientProvider = Provider<BackendDioClient>((ref) {
  final tokenStorage = ref.watch(tokenStorageProvider);

  return BackendDioClient(
    tokenStorage: tokenStorage,
    onUnauthorized: (message) {
      ref.read(sessionExpiryProvider.notifier).notifyExpired(message: message);
    },
  );
});
