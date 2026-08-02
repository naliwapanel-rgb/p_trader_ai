import '../data/backend_price_alert.dart';

class BackendPriceAlertState {
  const BackendPriceAlertState({
    required this.alerts,
    required this.isLoading,
    required this.isMutating,
    required this.hasLoaded,
    this.errorMessage,
    this.infoMessage,
  });

  const BackendPriceAlertState.initial()
    : alerts = const <BackendPriceAlert>[],
      isLoading = false,
      isMutating = false,
      hasLoaded = false,
      errorMessage = null,
      infoMessage = null;

  final List<BackendPriceAlert> alerts;
  final bool isLoading;
  final bool isMutating;
  final bool hasLoaded;
  final String? errorMessage;
  final String? infoMessage;

  List<BackendPriceAlert> get enabledAlerts {
    return alerts.where((alert) => alert.isEnabled).toList(growable: false);
  }

  List<BackendPriceAlert> get triggeredAlerts {
    return alerts.where((alert) => alert.triggered).toList(growable: false);
  }

  BackendPriceAlert? findById(int alertId) {
    for (final alert in alerts) {
      if (alert.id == alertId) {
        return alert;
      }
    }

    return null;
  }

  BackendPriceAlertState copyWith({
    List<BackendPriceAlert>? alerts,
    bool? isLoading,
    bool? isMutating,
    bool? hasLoaded,
    String? errorMessage,
    String? infoMessage,
    bool clearError = false,
    bool clearInfo = false,
  }) {
    return BackendPriceAlertState(
      alerts: alerts ?? this.alerts,
      isLoading: isLoading ?? this.isLoading,
      isMutating: isMutating ?? this.isMutating,
      hasLoaded: hasLoaded ?? this.hasLoaded,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      infoMessage: clearInfo ? null : infoMessage ?? this.infoMessage,
    );
  }
}
