import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/app_card.dart';
import 'data/backend_price_alert.dart';
import 'providers/alert_monitor_provider.dart';
import 'providers/backend_price_alert_provider.dart';
import 'providers/backend_price_alert_state.dart';
import 'widgets/add_alert_dialog.dart';

class AlertsScreen extends ConsumerStatefulWidget {
  const AlertsScreen({super.key});

  @override
  ConsumerState<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends ConsumerState<AlertsScreen> {
  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }

      ref.read(backendPriceAlertProvider.notifier).loadAlerts();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(backendPriceAlertProvider);
    final triggeredAlerts = ref.watch(triggeredAlertsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Price Alerts'),
        actions: [
          IconButton(
            tooltip: 'Refresh alerts',
            onPressed: state.isLoading
                ? null
                : () {
                    ref
                        .read(backendPriceAlertProvider.notifier)
                        .loadAlerts(force: true);
                  },
            icon: state.isLoading
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
          ),
          IconButton(
            tooltip: 'Create price alert',
            onPressed: state.isMutating ? null : _openAddAlertDialog,
            icon: const Icon(Icons.add_alert_outlined),
          ),
        ],
      ),
      body: _buildBody(context, state, triggeredAlerts),
    );
  }

  Widget _buildBody(
    BuildContext context,
    BackendPriceAlertState state,
    List<BackendPriceAlert> triggeredAlerts,
  ) {
    if (state.isLoading && !state.hasLoaded) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.errorMessage != null && state.alerts.isEmpty) {
      return _errorState(context, state.errorMessage!);
    }

    return RefreshIndicator(
      onRefresh: () {
        return ref
            .read(backendPriceAlertProvider.notifier)
            .loadAlerts(force: true);
      },
      child: CustomScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        slivers: [
          if (triggeredAlerts.isNotEmpty)
            SliverToBoxAdapter(child: _triggeredBanner(triggeredAlerts.length)),
          if (state.errorMessage != null)
            SliverToBoxAdapter(
              child: _errorBanner(context, state.errorMessage!),
            ),
          if (state.alerts.isEmpty)
            SliverFillRemaining(hasScrollBody: false, child: _emptyState())
          else
            SliverPadding(
              padding: const EdgeInsets.all(AppSpacing.md),
              sliver: SliverList.separated(
                itemCount: state.alerts.length,
                separatorBuilder: (_, _) =>
                    const SizedBox(height: AppSpacing.sm),
                itemBuilder: (context, index) {
                  return _alertTile(context, state.alerts[index], state);
                },
              ),
            ),
        ],
      ),
    );
  }

  Widget _triggeredBanner(int count) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.md,
        AppSpacing.md,
        0,
      ),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.notifications_active, color: AppColors.warning),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              '$count price alert(s) have reached '
              'their target.',
              style: AppTextStyles.title,
            ),
          ),
        ],
      ),
    );
  }

  Widget _errorBanner(BuildContext context, String message) {
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.md,
        AppSpacing.md,
        0,
      ),
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.errorContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(
            Icons.error_outline,
            color: Theme.of(context).colorScheme.onErrorContainer,
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(
            child: Text(
              message,
              style: TextStyle(
                color: Theme.of(context).colorScheme.onErrorContainer,
              ),
            ),
          ),
          TextButton(
            onPressed: () {
              ref
                  .read(backendPriceAlertProvider.notifier)
                  .loadAlerts(force: true);
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _errorState(BuildContext context, String message) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: AppCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.cloud_off_outlined,
                size: 56,
                color: Theme.of(context).colorScheme.error,
              ),
              const SizedBox(height: AppSpacing.md),
              Text('Price alerts unavailable', style: AppTextStyles.title),
              const SizedBox(height: AppSpacing.sm),
              Text(
                message,
                textAlign: TextAlign.center,
                style: AppTextStyles.body,
              ),
              const SizedBox(height: AppSpacing.md),
              FilledButton.icon(
                onPressed: () {
                  ref
                      .read(backendPriceAlertProvider.notifier)
                      .loadAlerts(force: true);
                },
                icon: const Icon(Icons.refresh),
                label: const Text('Try again'),
              ),
            ],
          ),
        ),
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
                'Create an authenticated alert for an '
                'important market price.',
                textAlign: TextAlign.center,
                style: AppTextStyles.body,
              ),
              const SizedBox(height: AppSpacing.md),
              FilledButton.icon(
                onPressed: _openAddAlertDialog,
                icon: const Icon(Icons.add_alert_outlined),
                label: const Text('Create alert'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _alertTile(
    BuildContext context,
    BackendPriceAlert alert,
    BackendPriceAlertState state,
  ) {
    final conditionText = alert.condition == BackendPriceAlertCondition.above
        ? 'Above'
        : 'Below';

    return AppCard(
      child: Row(
        children: [
          CircleAvatar(
            backgroundColor: AppColors.primary.withValues(alpha: 0.15),
            child: Icon(
              alert.condition == BackendPriceAlertCondition.above
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
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        alert.baseAssetSymbol,
                        style: AppTextStyles.title,
                      ),
                    ),
                    if (alert.triggered)
                      const Icon(
                        Icons.notifications_active,
                        size: 18,
                        color: AppColors.warning,
                      ),
                  ],
                ),
                const SizedBox(height: 2),
                Text(
                  '$conditionText '
                  '\$${_formatPrice(alert.targetPrice)}',
                  style: AppTextStyles.body,
                ),
                const SizedBox(height: 2),
                Text(
                  '${alert.exchange} • ${alert.symbol}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          Switch(
            value: alert.isEnabled,
            onChanged: state.isMutating ? null : (_) => _toggleAlert(alert),
          ),
          IconButton(
            tooltip: 'Delete alert',
            onPressed: state.isMutating ? null : () => _deleteAlert(alert),
            icon: const Icon(Icons.delete_outline),
          ),
        ],
      ),
    );
  }

  Future<void> _openAddAlertDialog() async {
    final created = await showDialog<bool>(
      context: context,
      builder: (_) => const AddAlertDialog(),
    );

    if (created == true && mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Price alert created.')));
    }
  }

  Future<void> _toggleAlert(BackendPriceAlert alert) async {
    final updated = await ref
        .read(backendPriceAlertProvider.notifier)
        .toggleEnabled(alert.id);

    if (updated == null && mounted) {
      final message = ref.read(backendPriceAlertProvider).errorMessage;

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message ?? 'The price alert could not be updated.'),
        ),
      );
    }
  }

  Future<void> _deleteAlert(BackendPriceAlert alert) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Delete Price Alert'),
          content: Text(
            'Delete the ${alert.baseAssetSymbol} '
            'price alert?',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(dialogContext, false);
              },
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.pop(dialogContext, true);
              },
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !mounted) {
      return;
    }

    final deleted = await ref
        .read(backendPriceAlertProvider.notifier)
        .deleteAlert(alert.id);

    if (!mounted) {
      return;
    }

    final state = ref.read(backendPriceAlertProvider);

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          deleted
              ? state.infoMessage ?? 'Price alert deleted.'
              : state.errorMessage ?? 'The price alert could not be deleted.',
        ),
      ),
    );
  }

  String _formatPrice(double value) {
    if (value >= 1) {
      return value.toStringAsFixed(2);
    }

    return value.toStringAsFixed(6);
  }
}
