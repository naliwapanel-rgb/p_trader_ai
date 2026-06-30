import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class PerformanceChart extends StatelessWidget {
  const PerformanceChart({super.key});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 220,
      child: LineChart(
        LineChartData(
          borderData: FlBorderData(show: false),
          gridData: FlGridData(show: false),
          titlesData: FlTitlesData(show: false),
          lineBarsData: [
            LineChartBarData(
              isCurved: true,
              color: AppColors.primary,
              barWidth: 4,
              spots: const [
                FlSpot(0, 3),
                FlSpot(1, 2.6),
                FlSpot(2, 4),
                FlSpot(3, 3.5),
                FlSpot(4, 5),
                FlSpot(5, 4.6),
                FlSpot(6, 6),
              ],
              belowBarData: BarAreaData(
                show: true,
                color: AppColors.primary.withValues(alpha: 0.18),
              ),
              dotData: FlDotData(show: false),
            ),
          ],
        ),
      ),
    );
  }
}
