import '../data/backend_notification_preferences.dart';

class BackendNotificationPreferencesState {
  const BackendNotificationPreferencesState({
    required this.isLoading,
    required this.isMutating,
    required this.hasLoaded,
    this.preferences,
    this.errorMessage,
    this.infoMessage,
  });

  const BackendNotificationPreferencesState.initial()
    : isLoading = false,
      isMutating = false,
      hasLoaded = false,
      preferences = null,
      errorMessage = null,
      infoMessage = null;

  final bool isLoading;
  final bool isMutating;
  final bool hasLoaded;
  final BackendNotificationPreferences? preferences;
  final String? errorMessage;
  final String? infoMessage;

  BackendNotificationPreferencesState copyWith({
    bool? isLoading,
    bool? isMutating,
    bool? hasLoaded,
    BackendNotificationPreferences? preferences,
    String? errorMessage,
    String? infoMessage,
    bool clearPreferences = false,
    bool clearError = false,
    bool clearInfo = false,
  }) {
    return BackendNotificationPreferencesState(
      isLoading: isLoading ?? this.isLoading,
      isMutating: isMutating ?? this.isMutating,
      hasLoaded: hasLoaded ?? this.hasLoaded,
      preferences: clearPreferences ? null : preferences ?? this.preferences,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      infoMessage: clearInfo ? null : infoMessage ?? this.infoMessage,
    );
  }
}
