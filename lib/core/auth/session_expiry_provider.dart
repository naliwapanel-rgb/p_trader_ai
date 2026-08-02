import 'package:flutter_riverpod/flutter_riverpod.dart';

class SessionExpiryState {
  const SessionExpiryState({required this.eventId, this.message});

  const SessionExpiryState.initial() : eventId = 0, message = null;

  final int eventId;
  final String? message;
}

class SessionExpiryNotifier extends Notifier<SessionExpiryState> {
  @override
  SessionExpiryState build() {
    return const SessionExpiryState.initial();
  }

  void notifyExpired({
    String message = 'Your session has expired. Please log in again.',
  }) {
    state = SessionExpiryState(eventId: state.eventId + 1, message: message);
  }
}

final sessionExpiryProvider =
    NotifierProvider<SessionExpiryNotifier, SessionExpiryState>(
      SessionExpiryNotifier.new,
    );
