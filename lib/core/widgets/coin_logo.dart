import 'package:flutter/material.dart';

class CoinLogo extends StatelessWidget {
  final String symbol;
  final double size;

  const CoinLogo({super.key, required this.symbol, this.size = 42});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(size / 2),
        color: Colors.white..withValues(alpha: 0.15),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(size / 2),
        child: Image.asset(
          'assets/images/coins/${symbol.toLowerCase()}.png',
          fit: BoxFit.cover,
          errorBuilder: (context, error, stackTrace) {
            return Center(
              child: Text(
                symbol.toUpperCase(),
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: size * 0.32,
                  color: Colors.white,
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
