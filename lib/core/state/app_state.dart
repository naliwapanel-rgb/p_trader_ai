class AppState {
  const AppState({
    required this.isBackendConnected,
    required this.isAiReady,
    required this.isArbitrageScannerReady,
    required this.lastSyncedAt,
  });

  final bool isBackendConnected;
  final bool isAiReady;
  final bool isArbitrageScannerReady;
  final DateTime? lastSyncedAt;

  AppState copyWith({
    bool? isBackendConnected,
    bool? isAiReady,
    bool? isArbitrageScannerReady,
    DateTime? lastSyncedAt,
  }) {
    return AppState(
      isBackendConnected: isBackendConnected ?? this.isBackendConnected,
      isAiReady: isAiReady ?? this.isAiReady,
      isArbitrageScannerReady:
          isArbitrageScannerReady ?? this.isArbitrageScannerReady,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
    );
  }
}
