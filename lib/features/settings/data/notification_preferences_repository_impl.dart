import '../domain/notification_preferences_repository.dart';
import 'backend_notification_preferences.dart';
import 'notification_preferences_remote_data_source.dart';

class NotificationPreferencesRepositoryImpl
    implements NotificationPreferencesRepository {
  const NotificationPreferencesRepositoryImpl({
    required NotificationPreferencesRemoteDataSource remoteDataSource,
  }) : _remoteDataSource = remoteDataSource;

  final NotificationPreferencesRemoteDataSource _remoteDataSource;

  @override
  Future<BackendNotificationPreferences> getPreferences() {
    return _remoteDataSource.getPreferences();
  }

  @override
  Future<BackendNotificationPreferences> updatePreferences(
    NotificationPreferenceUpdate update,
  ) {
    return _remoteDataSource.updatePreferences(update);
  }
}
