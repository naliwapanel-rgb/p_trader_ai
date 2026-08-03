import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import 'data/backend_trading_bot.dart';
import 'providers/backend_trading_bot_provider.dart';
import 'providers/backend_trading_bot_state.dart';
import 'widgets/add_trading_bot_dialog.dart';

class BotsScreen extends ConsumerStatefulWidget {
  const BotsScreen({super.key});

  @override
  ConsumerState<BotsScreen> createState() => _BotsScreenState();
}

class _BotsScreenState extends ConsumerState<BotsScreen> {
  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }

      final state = ref.read(backendTradingBotProvider);

      if (!state.hasLoaded && !state.isLoading) {
        ref.read(backendTradingBotProvider.notifier).loadBots();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(backendTradingBotProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Trading Bots'),
        actions: [
          IconButton(
            tooltip: 'Refresh trading bots',
            onPressed: state.isLoading
                ? null
                : () => ref.read(backendTradingBotProvider.notifier).loadBots(),
            icon: const Icon(Icons.refresh),
          ),
          IconButton(
            tooltip: 'Create trading bot',
            onPressed: state.isMutating
                ? null
                : () => _showCreateDialog(context),
            icon: const Icon(Icons.add_circle_outline),
          ),
        ],
      ),
      body: RefreshIndicator(
        color: AppColors.primary,
        backgroundColor: AppColors.card,
        onRefresh: () =>
            ref.read(backendTradingBotProvider.notifier).loadBots(),
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(AppSpacing.md),
          children: [
            if (state.errorMessage != null) _errorBanner(state.errorMessage!),
            if (state.infoMessage != null) _infoBanner(state.infoMessage!),
            if (state.isLoading && !state.hasLoaded)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 100),
                child: Center(child: CircularProgressIndicator()),
              )
            else ...[
              _summary(state),
              const SizedBox(height: AppSpacing.lg),
              Row(
                children: [
                  const Expanded(
                    child: Text('My Bots', style: AppTextStyles.title),
                  ),
                  Text('${state.bots.length} total', style: AppTextStyles.body),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              if (state.bots.isEmpty)
                _emptyState(context)
              else
                ...state.bots.map((bot) => _botCard(state, bot)),
              const SizedBox(height: AppSpacing.xl),
            ],
          ],
        ),
      ),
    );
  }

  Widget _summary(BackendTradingBotState state) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final active = _summaryCard(
          title: 'Active Bots',
          value: '${state.activeBots.length}',
          subtitle: 'Running or paused',
          icon: Icons.smart_toy_outlined,
          color: AppColors.primary,
        );

        final running = _summaryCard(
          title: 'Running',
          value: '${state.runningBots.length}',
          subtitle: 'Executing now',
          icon: Icons.play_circle_outline,
          color: AppColors.success,
        );

        final safe = _summaryCard(
          title: 'Safe Mode',
          value:
              '${state.bots.where((bot) => bot.paperTrading || bot.dryRun).length}',
          subtitle: 'Paper or dry run',
          icon: Icons.shield_outlined,
          color: AppColors.warning,
        );

        if (constraints.maxWidth < 720) {
          return Column(
            children: [
              active,
              const SizedBox(height: AppSpacing.sm),
              running,
              const SizedBox(height: AppSpacing.sm),
              safe,
            ],
          );
        }

        return Row(
          children: [
            Expanded(child: active),
            const SizedBox(width: AppSpacing.md),
            Expanded(child: running),
            const SizedBox(width: AppSpacing.md),
            Expanded(child: safe),
          ],
        );
      },
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
      child: Row(
        children: [
          CircleAvatar(
            radius: 22,
            backgroundColor: color.withValues(alpha: 0.15),
            child: Icon(icon, color: color),
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: AppTextStyles.body),
                Text(value, style: AppTextStyles.heading),
                Text(subtitle, style: TextStyle(color: color, fontSize: 12)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _emptyState(BuildContext context) {
    return GlassCard(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.xl),
        child: Column(
          children: [
            const Icon(
              Icons.smart_toy_outlined,
              size: 58,
              color: AppColors.textSecondary,
            ),
            const SizedBox(height: AppSpacing.md),
            const Text('No trading bots yet', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Your authenticated trading bots '
              'will appear here.',
              textAlign: TextAlign.center,
              style: AppTextStyles.body,
            ),
            const SizedBox(height: AppSpacing.lg),
            FilledButton.icon(
              key: const Key('create-first-bot-button'),
              onPressed: () => _showCreateDialog(context),
              icon: const Icon(Icons.add),
              label: const Text('Create First Bot'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _botCard(BackendTradingBotState state, BackendTradingBot bot) {
    final color = _statusColor(bot.status);
    final busy = state.isBotBusy(bot.id);

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 23,
                  backgroundColor: color.withValues(alpha: 0.15),
                  child: Icon(Icons.smart_toy_outlined, color: color),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(bot.name, style: AppTextStyles.title),
                      const SizedBox(height: AppSpacing.xs),
                      Text(
                        '${bot.symbol} • '
                        '${bot.timeframe.backendValue} • '
                        '${bot.category.backendValue.toUpperCase()}',
                        style: AppTextStyles.body,
                      ),
                    ],
                  ),
                ),
                _statusChip(bot.status.backendValue, color),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                _metricChip(
                  'Strategy',
                  _strategyLabel(bot.strategyType),
                  AppColors.primary,
                ),
                _metricChip(
                  'Risk',
                  '${bot.riskPerTradePercent.toStringAsFixed(2)}%',
                  AppColors.warning,
                ),
                _metricChip(
                  'Max Position',
                  '\$${bot.maxPositionValueUsd.toStringAsFixed(2)}',
                  AppColors.success,
                ),
                if (bot.paperTrading)
                  _metricChip('Mode', 'Paper', AppColors.primary),
                if (bot.dryRun)
                  _metricChip('Safety', 'Dry Run', AppColors.success),
              ],
            ),
            if (bot.lastError != null) ...[
              const SizedBox(height: AppSpacing.md),
              Text(
                bot.lastError!,
                style: const TextStyle(color: AppColors.danger),
              ),
            ],
            const SizedBox(height: AppSpacing.md),
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                OutlinedButton.icon(
                  onPressed: busy ? null : () => _showDetails(bot),
                  icon: const Icon(Icons.info_outline),
                  label: const Text('Details'),
                ),
                for (final action in _lifecycleActions(bot.status))
                  FilledButton.tonalIcon(
                    key: Key('bot-${bot.id}-${action.routeValue}-button'),
                    onPressed: busy
                        ? null
                        : () => _performLifecycle(bot.id, action),
                    icon: Icon(_actionIcon(action)),
                    label: Text(_actionLabel(action)),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _metricChip(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(50),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Text(
        '$label: $value',
        style: TextStyle(
          color: color,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _statusChip(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(50),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _errorBanner(String message) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.sm),
        decoration: BoxDecoration(
          color: AppColors.danger.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          border: Border.all(color: AppColors.danger.withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline, color: AppColors.danger),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: AppColors.danger),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoBanner(String message) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: Container(
        padding: const EdgeInsets.all(AppSpacing.sm),
        decoration: BoxDecoration(
          color: AppColors.success.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(AppSpacing.radius),
          border: Border.all(color: AppColors.success.withValues(alpha: 0.4)),
        ),
        child: Row(
          children: [
            const Icon(Icons.check_circle_outline, color: AppColors.success),
            const SizedBox(width: AppSpacing.sm),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(color: AppColors.success),
              ),
            ),
            IconButton(
              tooltip: 'Dismiss message',
              onPressed: () =>
                  ref.read(backendTradingBotProvider.notifier).clearMessages(),
              icon: const Icon(Icons.close),
              color: AppColors.success,
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showCreateDialog(BuildContext context) async {
    ref.read(backendTradingBotProvider.notifier).clearMessages();

    await showDialog<BackendTradingBot>(
      context: context,
      builder: (_) => const AddTradingBotDialog(),
    );
  }

  Future<void> _performLifecycle(
    int botId,
    TradingBotLifecycleAction action,
  ) async {
    await ref
        .read(backendTradingBotProvider.notifier)
        .performLifecycle(botId: botId, action: action);
  }

  Future<void> _showDetails(BackendTradingBot bot) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.background,
      builder: (sheetContext) => SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(bot.name, style: AppTextStyles.heading),
              const SizedBox(height: AppSpacing.md),
              _detailRow('Status', bot.status.backendValue),
              _detailRow('Symbol', bot.symbol),
              _detailRow('Strategy', _strategyLabel(bot.strategyType)),
              _detailRow('Timeframe', bot.timeframe.backendValue),
              _detailRow('Paper trading', bot.paperTrading ? 'Yes' : 'No'),
              _detailRow('Dry run', bot.dryRun ? 'Yes' : 'No'),
              _detailRow(
                'Maximum position',
                '\$${bot.maxPositionValueUsd.toStringAsFixed(2)}',
              ),
              const SizedBox(height: AppSpacing.lg),
              SizedBox(
                width: double.infinity,
                child: FilledButton(
                  onPressed: () => Navigator.pop(sheetContext),
                  child: const Text('Close'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _detailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        children: [
          Expanded(child: Text(label, style: AppTextStyles.body)),
          const SizedBox(width: AppSpacing.md),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<TradingBotLifecycleAction> _lifecycleActions(TradingBotStatus status) {
    return switch (status) {
      TradingBotStatus.draft => const <TradingBotLifecycleAction>[
        TradingBotLifecycleAction.prepare,
      ],
      TradingBotStatus.stopped => const <TradingBotLifecycleAction>[
        TradingBotLifecycleAction.start,
      ],
      TradingBotStatus.running => const <TradingBotLifecycleAction>[
        TradingBotLifecycleAction.pause,
        TradingBotLifecycleAction.stop,
      ],
      TradingBotStatus.paused => const <TradingBotLifecycleAction>[
        TradingBotLifecycleAction.resume,
      ],
      TradingBotStatus.error => const <TradingBotLifecycleAction>[
        TradingBotLifecycleAction.stop,
      ],
      TradingBotStatus.starting ||
      TradingBotStatus.archived => const <TradingBotLifecycleAction>[],
    };
  }

  String _actionLabel(TradingBotLifecycleAction action) {
    return switch (action) {
      TradingBotLifecycleAction.prepare => 'Prepare',
      TradingBotLifecycleAction.start => 'Start',
      TradingBotLifecycleAction.pause => 'Pause',
      TradingBotLifecycleAction.resume => 'Resume',
      TradingBotLifecycleAction.stop => 'Stop',
    };
  }

  IconData _actionIcon(TradingBotLifecycleAction action) {
    return switch (action) {
      TradingBotLifecycleAction.prepare => Icons.build_outlined,
      TradingBotLifecycleAction.start => Icons.play_arrow,
      TradingBotLifecycleAction.pause => Icons.pause,
      TradingBotLifecycleAction.resume => Icons.play_arrow,
      TradingBotLifecycleAction.stop => Icons.stop,
    };
  }

  Color _statusColor(TradingBotStatus status) {
    return switch (status) {
      TradingBotStatus.running => AppColors.success,
      TradingBotStatus.starting || TradingBotStatus.paused => AppColors.warning,
      TradingBotStatus.error => AppColors.danger,
      TradingBotStatus.draft => AppColors.primary,
      TradingBotStatus.stopped ||
      TradingBotStatus.archived => AppColors.textSecondary,
    };
  }

  String _strategyLabel(TradingBotStrategyType strategy) {
    return switch (strategy) {
      TradingBotStrategyType.ruleBased => 'Rule Based',
      TradingBotStrategyType.momentum => 'Momentum',
      TradingBotStrategyType.trend => 'Trend',
      TradingBotStrategyType.meanReversion => 'Mean Reversion',
      TradingBotStrategyType.scalping => 'Scalping',
      TradingBotStrategyType.grid => 'Grid',
      TradingBotStrategyType.dca => 'DCA',
      TradingBotStrategyType.arbitrage => 'Arbitrage',
      TradingBotStrategyType.custom => 'Custom',
    };
  }
}
