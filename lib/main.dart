import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme/app_theme.dart';
import 'features/splash/splash_screen.dart';

void main() {
  runApp(const ProviderScope(child: PTraderAI()));
}

class PTraderAI extends StatelessWidget {
  const PTraderAI({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'P-TRADER AI',
      theme: AppTheme.darkTheme,
      home: const SplashScreen(),
    );
  }
}
