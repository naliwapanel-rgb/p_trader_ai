import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme/app_theme.dart';
import 'features/splash/splash_screen.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core/providers/local_storage_provider.dart';
import 'features/auth/session_expiry_listener.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  final sharedPreferences = await SharedPreferences.getInstance();

  runApp(
    ProviderScope(
      overrides: [
        sharedPreferencesProvider.overrideWithValue(sharedPreferences),
      ],
      child: const PTraderAI(),
    ),
  );
}

class PTraderAI extends StatelessWidget {
  const PTraderAI({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      navigatorKey: rootNavigatorKey,
      builder: (context, child) {
        return AuthSessionExpiryListener(
          child: child ?? const SizedBox.shrink(),
        );
      },
      debugShowCheckedModeBanner: false,
      title: 'P-TRADER AI',
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}
