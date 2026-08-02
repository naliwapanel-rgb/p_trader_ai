import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/backend_notification_preferences.dart';
import '../data/notification_preferences_remote_data_source.dart';
import '../data/notification_preferences_repository_impl.dart';
import '../domain/notification_preferences_repository.dart';
import 'backend_notification_preferences_state.dart';

final notificationPreferencesRemoteDataSourceProvider =
    Provider<NotificationPreferencesRemoteDataSource>((ref) {
      return DioNotificationPreferencesRemoteDataSource(
        ref.watch(backendDioClientProvider).dio,
      );
    });

final notificationPreferencesRepositoryProvider =
    Provider<NotificationPreferencesRepository>((ref) {
      return NotificationPreferencesRepositoryImpl(
        remoteDataSource: ref.watch(
          notificationPreferencesRemoteDataSourceProvider,
        ),
      );
    });

final backendNotificationPreferencesProvider =
    NotifierProvider<
      BackendNotificationPreferencesNotifier,
      BackendNotificationPreferencesState
    >(BackendNotificationPreferencesNotifier.new);

class BackendNotificationPreferencesNotifier
    extends Notifier<BackendNotificationPreferencesState> {
  @override
  BackendNotificationPreferencesState build() {
    return const BackendNotificationPreferencesState.initial();
  }

  Future<void> loadPreferences({bool force = false}) async {
    if (state.isLoading || (state.hasLoaded && !force)) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearInfo: true);

    try {
      final preferences = await ref
          .read(notificationPreferencesRepositoryProvider)
          .getPreferences();

      state = state.copyWith(
        preferences: preferences,
        isLoading: false,
        hasLoaded: true,
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(
        isLoading: false,
        hasLoaded: true,
        errorMessage: error.message,
      );
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        hasLoaded: true,
        errorMessage: 'Notification preferences could not be loaded.',
      );
    }
  }

  Future<BackendNotificationPreferences?> updatePreferences(
    NotificationPreferenceUpdate update,
  ) async {
    if (state.isMutating) {
      return null;
    }

    if (!update.hasChanges) {
      state = state.copyWith(
        errorMessage: 'At least one notification preference must be supplied.',
        clearInfo: true,
      );
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      final preferences = await ref
          .read(notificationPreferencesRepositoryProvider)
          .updatePreferences(update);

      state = state.copyWith(
        preferences: preferences,
        isMutating: false,
        hasLoaded: true,
        infoMessage: 'Notification preferences updated.',
        clearError: true,
      );

      return preferences;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'Notification preferences could not be updated.',
      );
      return null;
    }
  }

  Future<BackendNotificationPreferences?> setEmailEnabled(bool value) {
    return updatePreferences(NotificationPreferenceUpdate(emailEnabled: value));
  }

  Future<BackendNotificationPreferences?> setPushEnabled(bool value) {
    return updatePreferences(NotificationPreferenceUpdate(pushEnabled: value));
  }

  Future<BackendNotificationPreferences?> setSoundEnabled(bool value) {
    return updatePreferences(NotificationPreferenceUpdate(soundEnabled: value));
  }

  Future<BackendNotificationPreferences?> setPriceAlerts(bool value) {
    return updatePreferences(NotificationPreferenceUpdate(priceAlerts: value));
  }

  Future<BackendNotificationPreferences?> setArbitrageAlerts(bool value) {
    return updatePreferences(
      NotificationPreferenceUpdate(arbitrageAlerts: value),
    );
  }

  Future<BackendNotificationPreferences?> setAiAlerts(bool value) {
    return updatePreferences(NotificationPreferenceUpdate(aiAlerts: value));
  }

  Future<BackendNotificationPreferences?> setNewsAlerts(bool value) {
    return updatePreferences(NotificationPreferenceUpdate(newsAlerts: value));
  }

  void clearMessages() {
    state = state.copyWith(clearError: true, clearInfo: true);
  }
}
