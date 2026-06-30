import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class CoinAvatar extends StatelessWidget {
  final String symbol;

  const CoinAvatar({super.key, required this.symbol});

  @override
  Widget build(BuildContext context) {
    return CircleAvatar(
      radius: 24,
      backgroundColor: AppColors.primary..withValues(alpha: 0.15),
      child: Text(
        symbol,
        style: const TextStyle(
          color: AppColors.primary,
          fontWeight: FontWeight.bold,
          fontSize: 18,
        ),
      ),
    );
  }
}
