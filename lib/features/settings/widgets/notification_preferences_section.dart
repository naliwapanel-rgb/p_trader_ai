import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_colors.dart';
import '../../../core/theme/app_spacing.dart';
import '../../../core/theme/app_text_styles.dart';
import '../../../core/widgets/glass_card.dart';
import '../data/backend_notification_preferences.dart';
import '../providers/backend_notification_preferences_provider.dart';
import '../providers/backend_notification_preferences_state.dart';

class NotificationPreferencesSection extends ConsumerStatefulWidget {
  const NotificationPreferencesSection({required this.enabled, super.key});

  final bool enabled;

  @override
  ConsumerState<NotificationPreferencesSection> createState() {
    return _NotificationPreferencesSectionState();
  }
}

class _NotificationPreferencesSectionState
    extends ConsumerState<NotificationPreferencesSection> {
  @override
  void initState() {
    super.initState();
    _scheduleLoad();
  }

  @override
  void didUpdateWidget(NotificationPreferencesSection oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (!oldWidget.enabled && widget.enabled) {
      _scheduleLoad();
    }
  }

  void _scheduleLoad() {
    if (!widget.enabled) {
      return;
    }

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }

      ref
          .read(backendNotificationPreferencesProvider.notifier)
          .loadPreferences();
    });
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(backendNotificationPreferencesProvider);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Expanded(
              child: Text(
                'Notification Preferences',
                style: AppTextStyles.title,
              ),
            ),
            IconButton(
              tooltip: 'Refresh notification settings',
              onPressed: !widget.enabled || state.isLoading || state.isMutating
                  ? null
                  : () {
                      ref
                          .read(backendNotificationPreferencesProvider.notifier)
                          .loadPreferences(force: true);
                    },
              icon: state.isLoading
                  ? const SizedBox.square(
                      dimension: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.refresh),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.sm),
        if (!widget.enabled)
          _messageCard(
            icon: Icons.lock_outline,
            message: 'Sign in to manage notifications.',
          )
        else if (state.isLoading && state.preferences == null)
          _loadingCard()
        else if (state.errorMessage != null && state.preferences == null)
          _errorCard(state)
        else if (state.preferences != null) ...[
          _preferencesCard(state, state.preferences!),
          if (state.errorMessage != null) ...[
            const SizedBox(height: AppSpacing.sm),
            _inlineError(state.errorMessage!),
          ],
        ] else
          _messageCard(
            icon: Icons.notifications_none,
            message: 'Notification settings are not available.',
          ),
      ],
    );
  }

  Widget _loadingCard() {
    return const GlassCard(
      child: Row(
        children: [
          SizedBox.square(
            dimension: 22,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
          SizedBox(width: AppSpacing.md),
          Expanded(
            child: Text(
              'Loading notification preferences...',
              style: AppTextStyles.body,
            ),
          ),
        ],
      ),
    );
  }

  Widget _errorCard(BackendNotificationPreferencesState state) {
    return GlassCard(
      child: Column(
        children: [
          const Icon(
            Icons.cloud_off_outlined,
            color: AppColors.danger,
            size: 36,
          ),
          const SizedBox(height: AppSpacing.sm),
          const Text(
            'Notification settings unavailable',
            style: AppTextStyles.title,
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            state.errorMessage ?? 'The settings could not be loaded.',
            textAlign: TextAlign.center,
            style: AppTextStyles.body,
          ),
          const SizedBox(height: AppSpacing.md),
          FilledButton.icon(
            onPressed: state.isLoading
                ? null
                : () {
                    ref
                        .read(backendNotificationPreferencesProvider.notifier)
                        .loadPreferences(force: true);
                  },
            icon: const Icon(Icons.refresh),
            label: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _preferencesCard(
    BackendNotificationPreferencesState state,
    BackendNotificationPreferences preferences,
  ) {
    final notifier = ref.read(backendNotificationPreferencesProvider.notifier);

    final items = <_NotificationPreferenceItem>[
      _NotificationPreferenceItem(
        icon: Icons.email_outlined,
        title: 'Email Notifications',
        subtitle: 'Receive account and alert emails',
        value: preferences.emailEnabled,
        update: notifier.setEmailEnabled,
      ),
      _NotificationPreferenceItem(
        icon: Icons.notifications_active_outlined,
        title: 'Push Notifications',
        subtitle: 'Receive notifications on this device',
        value: preferences.pushEnabled,
        update: notifier.setPushEnabled,
      ),
      _NotificationPreferenceItem(
        icon: Icons.volume_up_outlined,
        title: 'Notification Sound',
        subtitle: 'Play a sound for notifications',
        value: preferences.soundEnabled,
        update: notifier.setSoundEnabled,
      ),
      _NotificationPreferenceItem(
        icon: Icons.price_change_outlined,
        title: 'Price Alerts',
        subtitle: 'Notify when price targets are reached',
        value: preferences.priceAlerts,
        update: notifier.setPriceAlerts,
      ),
      _NotificationPreferenceItem(
        icon: Icons.swap_horiz,
        title: 'Arbitrage Alerts',
        subtitle: 'Notify about arbitrage opportunities',
        value: preferences.arbitrageAlerts,
        update: notifier.setArbitrageAlerts,
      ),
      _NotificationPreferenceItem(
        icon: Icons.auto_awesome_outlined,
        title: 'AI Alerts',
        subtitle: 'Receive AI-generated trading insights',
        value: preferences.aiAlerts,
        update: notifier.setAiAlerts,
      ),
      _NotificationPreferenceItem(
        icon: Icons.newspaper_outlined,
        title: 'Market News',
        subtitle: 'Receive important market updates',
        value: preferences.newsAlerts,
        update: notifier.setNewsAlerts,
      ),
    ];

    return GlassCard(
      padding: EdgeInsets.zero,
      child: Column(
        children: [
          for (var index = 0; index < items.length; index++) ...[
            Material(
              type: MaterialType.transparency,
              child: SwitchListTile(
                secondary: CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.13),
                  child: Icon(
                    items[index].icon,
                    size: 18,
                    color: AppColors.primary,
                  ),
                ),
                title: Text(
                  items[index].title,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                subtitle: Text(
                  items[index].subtitle,
                  style: AppTextStyles.body,
                ),
                value: items[index].value,
                onChanged: state.isMutating
                    ? null
                    : (value) {
                        _updatePreference(() => items[index].update(value));
                      },
              ),
            ),
            if (index != items.length - 1)
              const Divider(color: AppColors.divider, height: 1, indent: 72),
          ],
        ],
      ),
    );
  }

  Widget _messageCard({required IconData icon, required String message}) {
    return GlassCard(
      child: Row(
        children: [
          Icon(icon, color: AppColors.textSecondary),
          const SizedBox(width: AppSpacing.md),
          Expanded(child: Text(message, style: AppTextStyles.body)),
        ],
      ),
    );
  }

  Widget _inlineError(String message) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.danger.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(AppSpacing.radius),
      ),
      child: Text(message, style: const TextStyle(color: AppColors.danger)),
    );
  }

  Future<void> _updatePreference(
    Future<BackendNotificationPreferences?> Function() update,
  ) async {
    final result = await update();

    if (!mounted || result != null) {
      return;
    }

    final message = ref
        .read(backendNotificationPreferencesProvider)
        .errorMessage;

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          message ?? 'The notification setting could not be updated.',
        ),
      ),
    );
  }
}

class _NotificationPreferenceItem {
  const _NotificationPreferenceItem({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.value,
    required this.update,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final bool value;

  final Future<BackendNotificationPreferences?> Function(bool value) update;
}
