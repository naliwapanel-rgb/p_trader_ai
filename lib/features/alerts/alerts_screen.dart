import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/app_card.dart';
import 'data/price_alert.dart';
import 'providers/price_alert_provider.dart';
import 'widgets/add_alert_dialog.dart';
import 'providers/alert_monitor_provider.dart';

class AlertsScreen extends ConsumerWidget {
  const AlertsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alerts = ref.watch(priceAlertsProvider);
    final triggeredAlerts = ref.watch(triggeredAlertsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Price Alerts'),
        actions: [
          IconButton(
            onPressed: () {
              showDialog(
                context: context,
                builder: (_) => const AddAlertDialog(),
              );
            },
            icon: const Icon(Icons.add_alert_outlined),
          ),
        ],
      ),
      body: Column(
        children: [
          if (triggeredAlerts.isNotEmpty)
            Container(
              width: double.infinity,
              margin: const EdgeInsets.all(AppSpacing.md),
              padding: const EdgeInsets.all(AppSpacing.md),
              decoration: BoxDecoration(
                color: AppColors.warning.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                '${triggeredAlerts.length} alert(s) triggered.',
                style: AppTextStyles.title,
              ),
            ),
          Expanded(
            child: alerts.isEmpty
                ? _emptyState()
                : ListView.builder(
                    padding: const EdgeInsets.all(AppSpacing.md),
                    itemCount: alerts.length,
                    itemBuilder: (context, index) {
                      final alert = alerts[index];
                      return _alertTile(alert);
                    },
                  ),
          ),
        ],
      ),
    );
  }

  Widget _emptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: AppCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(
                Icons.notifications_active_outlined,
                size: 64,
                color: AppColors.primary,
              ),
              const SizedBox(height: AppSpacing.md),
              Text('No price alerts yet', style: AppTextStyles.title),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Create alerts for important price levels and market movements.',
                textAlign: TextAlign.center,
                style: AppTextStyles.body,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _alertTile(PriceAlert alert) {
    final conditionText = alert.condition == PriceAlertCondition.above
        ? 'Above'
        : 'Below';

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: AppCard(
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: AppColors.primary.withValues(alpha: 0.15),
              child: Icon(
                alert.condition == PriceAlertCondition.above
                    ? Icons.trending_up
                    : Icons.trending_down,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(alert.symbol, style: AppTextStyles.title),
                  Text(
                    '$conditionText \$${alert.targetPrice.toStringAsFixed(2)}',
                    style: AppTextStyles.body,
                  ),
                ],
              ),
            ),
            Switch(value: alert.isEnabled, onChanged: null),
          ],
        ),
      ),
    );
  }
}
