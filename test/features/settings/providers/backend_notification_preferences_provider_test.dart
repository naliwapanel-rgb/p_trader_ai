import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/settings/data/backend_notification_preferences.dart';
import 'package:p_trader_ai/features/settings/domain/notification_preferences_repository.dart';
import 'package:p_trader_ai/features/settings/providers/backend_notification_preferences_provider.dart';

void main() {
  group('BackendNotificationPreferencesNotifier', () {
    test('loads authenticated preferences', () async {
      final repository = _FakeNotificationPreferencesRepository();

      final container = _container(repository);
      addTearDown(container.dispose);

      await container
          .read(backendNotificationPreferencesProvider.notifier)
          .loadPreferences();

      final state = container.read(backendNotificationPreferencesProvider);

      expect(repository.getCalls, 1);
      expect(state.hasLoaded, isTrue);
      expect(state.preferences?.emailEnabled, isTrue);
      expect(state.errorMessage, isNull);
    });

    test('does not reload without force', () async {
      final repository = _FakeNotificationPreferencesRepository();

      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(
        backendNotificationPreferencesProvider.notifier,
      );

      await notifier.loadPreferences();
      await notifier.loadPreferences();

      expect(repository.getCalls, 1);
    });

    test('updates one preference field', () async {
      final repository = _FakeNotificationPreferencesRepository();

      final container = _container(repository);
      addTearDown(container.dispose);

      final updated = await container
          .read(backendNotificationPreferencesProvider.notifier)
          .setPushEnabled(false);

      final state = container.read(backendNotificationPreferencesProvider);

      expect(repository.updateCalls, 1);
      expect(updated?.pushEnabled, isFalse);
      expect(state.preferences?.pushEnabled, isFalse);
      expect(state.infoMessage, 'Notification preferences updated.');
    });

    test('stores load errors', () async {
      final repository = _FakeNotificationPreferencesRepository(
        getError: const AppException('Unable to load preferences'),
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container
          .read(backendNotificationPreferencesProvider.notifier)
          .loadPreferences();

      final state = container.read(backendNotificationPreferencesProvider);

      expect(state.errorMessage, 'Unable to load preferences');
      expect(state.isLoading, isFalse);
    });

    test('preserves preferences after update error', () async {
      final repository = _FakeNotificationPreferencesRepository(
        updateError: const AppException('Update failed'),
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      final notifier = container.read(
        backendNotificationPreferencesProvider.notifier,
      );

      await notifier.loadPreferences();
      await notifier.setNewsAlerts(true);

      final state = container.read(backendNotificationPreferencesProvider);

      expect(state.errorMessage, 'Update failed');
      expect(state.preferences?.newsAlerts, isFalse);
      expect(state.isMutating, isFalse);
    });
  });
}

ProviderContainer _container(NotificationPreferencesRepository repository) {
  return ProviderContainer(
    overrides: [
      notificationPreferencesRepositoryProvider.overrideWithValue(repository),
    ],
  );
}

class _FakeNotificationPreferencesRepository
    implements NotificationPreferencesRepository {
  _FakeNotificationPreferencesRepository({this.getError, this.updateError});

  final AppException? getError;
  final AppException? updateError;

  int getCalls = 0;
  int updateCalls = 0;

  BackendNotificationPreferences current = BackendNotificationPreferences(
    id: 4,
    userId: 9,
    emailEnabled: true,
    pushEnabled: true,
    soundEnabled: true,
    priceAlerts: true,
    arbitrageAlerts: true,
    aiAlerts: true,
    newsAlerts: false,
    updatedAt: DateTime.utc(2026, 8, 3),
  );

  @override
  Future<BackendNotificationPreferences> getPreferences() async {
    getCalls += 1;

    final error = getError;

    if (error != null) {
      throw error;
    }

    return current;
  }

  @override
  Future<BackendNotificationPreferences> updatePreferences(
    NotificationPreferenceUpdate update,
  ) async {
    updateCalls += 1;

    final error = updateError;

    if (error != null) {
      throw error;
    }

    current = current.copyWith(
      emailEnabled: update.emailEnabled,
      pushEnabled: update.pushEnabled,
      soundEnabled: update.soundEnabled,
      priceAlerts: update.priceAlerts,
      arbitrageAlerts: update.arbitrageAlerts,
      aiAlerts: update.aiAlerts,
      newsAlerts: update.newsAlerts,
      updatedAt: DateTime.utc(2026, 8, 3, 1),
    );

    return current;
  }
}
