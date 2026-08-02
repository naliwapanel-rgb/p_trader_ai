import '../data/backend_notification_preferences.dart';

abstract interface class NotificationPreferencesRepository {
  Future<BackendNotificationPreferences> getPreferences();

  Future<BackendNotificationPreferences> updatePreferences(
    NotificationPreferenceUpdate update,
  );
}
