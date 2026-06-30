import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';

class BotsScreen extends StatelessWidget {
  const BotsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final bots = [
      {
        'name': 'Triangular AI',
        'type': 'Arbitrage Bot',
        'status': 'Running',
        'profit': '+\$35.40',
        'confidence': '93%',
        'icon': Icons.change_circle_outlined,
        'color': AppColors.primary,
        'active': true,
      },
      {
        'name': 'Scalper AI',
        'type': 'Short-term Bot',
        'status': 'Running',
        'profit': '+\$21.80',
        'confidence': '88%',
        'icon': Icons.bolt_outlined,
        'color': AppColors.success,
        'active': true,
      },
      {
        'name': 'Grid AI',
        'type': 'Grid Trading Bot',
        'status': 'Paused',
        'profit': '+\$5.20',
        'confidence': '74%',
        'icon': Icons.grid_view_outlined,
        'color': AppColors.warning,
        'active': false,
      },
      {
        'name': 'Cross Exchange',
        'type': 'Spread Scanner',
        'status': 'Offline',
        'profit': '\$0.00',
        'confidence': '0%',
        'icon': Icons.compare_arrows_outlined,
        'color': AppColors.danger,
        'active': false,
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Trading Bots'),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.add_circle_outline),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _summary(context),
            const SizedBox(height: AppSpacing.lg),
            const Text('My Bots', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            ...bots.map((bot) => _botCard(bot)),
            const SizedBox(height: AppSpacing.xl),
          ],
        ),
      ),
    );
  }

  Widget _summary(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _summaryCard(
            title: 'Active Bots',
            value: '3',
            subtitle: 'Running now',
            icon: Icons.smart_toy_outlined,
            color: AppColors.primary,
          ),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: _summaryCard(
            title: 'Profit Today',
            value: '+\$62.40',
            subtitle: '+2.14%',
            icon: Icons.trending_up,
            color: AppColors.success,
          ),
        ),
      ],
    );
  }

  Widget _summaryCard({
    required String title,
    required String value,
    required String subtitle,
    required IconData icon,
    required Color color,
  }) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 20,
            backgroundColor: color.withValues(alpha: 0.15),
            child: Icon(icon, color: color, size: 20),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(title, style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.xs),
          Text(value, style: AppTextStyles.heading),
          const SizedBox(height: AppSpacing.xs),
          Text(
            subtitle,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _botCard(Map<String, Object> bot) {
    final color = bot['color'] as Color;
    final active = bot['active'] as bool;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  radius: 24,
                  backgroundColor: color.withValues(alpha: 0.15),
                  child: Icon(bot['icon'] as IconData, color: color),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(bot['name'].toString(), style: AppTextStyles.title),
                      Text(bot['type'].toString(), style: AppTextStyles.body),
                    ],
                  ),
                ),
                Switch(
                  value: active,
                  activeThumbColor: AppColors.primary,
                  onChanged: (_) {},
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                _miniInfo(
                  label: 'Status',
                  value: bot['status'].toString(),
                  color: active ? AppColors.success : AppColors.warning,
                ),
                const SizedBox(width: AppSpacing.md),
                _miniInfo(
                  label: 'Profit',
                  value: bot['profit'].toString(),
                  color: AppColors.success,
                ),
                const SizedBox(width: AppSpacing.md),
                _miniInfo(
                  label: 'AI Confidence',
                  value: bot['confidence'].toString(),
                  color: color,
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            ClipRRect(
              borderRadius: BorderRadius.circular(50),
              child: LinearProgressIndicator(
                value: active ? 0.88 : 0.35,
                minHeight: 7,
                color: color,
                backgroundColor: AppColors.divider,
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () {},
                    style: OutlinedButton.styleFrom(
                      foregroundColor: AppColors.textPrimary,
                      side: const BorderSide(color: AppColors.divider),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AppSpacing.radius),
                      ),
                    ),
                    child: const Text('Details'),
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: FilledButton(
                    onPressed: () {},
                    style: FilledButton.styleFrom(
                      backgroundColor: color.withValues(alpha: 0.2),
                      foregroundColor: color,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(AppSpacing.radius),
                      ),
                    ),
                    child: const Text('Configure'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _miniInfo({
    required String label,
    required String value,
    required Color color,
  }) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.sm),
        decoration: BoxDecoration(
          color: AppColors.card,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: AppColors.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: AppTextStyles.body.copyWith(fontSize: 12)),
            const SizedBox(height: AppSpacing.xs),
            Text(
              value,
              style: TextStyle(color: color, fontWeight: FontWeight.bold),
            ),
          ],
        ),
      ),
    );
  }
}
