import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app_state.dart';

final appStateProvider = NotifierProvider<AppStateNotifier, AppState>(
  AppStateNotifier.new,
);

class AppStateNotifier extends Notifier<AppState> {
  @override
  AppState build() {
    return const AppState(
      isBackendConnected: false,
      isAiReady: false,
      isArbitrageScannerReady: false,
      lastSyncedAt: null,
    );
  }

  void setBackendConnected(bool value) {
    state = state.copyWith(
      isBackendConnected: value,
      lastSyncedAt: DateTime.now(),
    );
  }

  void setAiReady(bool value) {
    state = state.copyWith(isAiReady: value);
  }

  void setArbitrageScannerReady(bool value) {
    state = state.copyWith(isArbitrageScannerReady: value);
  }
}
