import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/auth/session_expiry_provider.dart';
import '../exchange_accounts/providers/exchange_account_provider.dart';
import '../portfolio/providers/live_portfolio_provider.dart';
import '../watchlist/providers/backend_watchlist_provider.dart';
import 'login_screen.dart';
import 'providers/auth_provider.dart';

final rootNavigatorKey = GlobalKey<NavigatorState>();

class AuthSessionExpiryListener extends ConsumerStatefulWidget {
  const AuthSessionExpiryListener({required this.child, super.key});

  final Widget child;

  @override
  ConsumerState<AuthSessionExpiryListener> createState() {
    return _AuthSessionExpiryListenerState();
  }
}

class _AuthSessionExpiryListenerState
    extends ConsumerState<AuthSessionExpiryListener> {
  bool _navigationScheduled = false;

  @override
  Widget build(BuildContext context) {
    ref.listen<SessionExpiryState>(sessionExpiryProvider, (previous, next) {
      if (next.eventId == 0 ||
          previous?.eventId == next.eventId ||
          _navigationScheduled) {
        return;
      }

      _navigationScheduled = true;

      final message = next.message?.trim().isNotEmpty == true
          ? next.message!.trim()
          : 'Your session has expired. '
                'Please log in again.';

      ref.read(authProvider.notifier).expireSession(message: message);

      // Clear user-specific provider state so another
      // login cannot briefly see the previous session's
      // exchange, portfolio, or watchlist information.
      ref.invalidate(exchangeAccountProvider);
      ref.invalidate(livePortfolioProvider);
      ref.invalidate(backendWatchlistProvider);

      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) {
          return;
        }

        final navigator = rootNavigatorKey.currentState;

        if (navigator == null) {
          _navigationScheduled = false;
          return;
        }

        navigator.pushAndRemoveUntil<void>(
          MaterialPageRoute<void>(builder: (_) => const LoginScreen()),
          (_) => false,
        );

        _navigationScheduled = false;
      });
    });

    return widget.child;
  }
}
