import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../auth/login_screen.dart';
import '../auth/providers/auth_provider.dart';
import '../auth/providers/auth_state.dart';
import 'change_password_screen.dart';
import 'edit_profile_screen.dart';

class SettingsScreen extends ConsumerWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    final user = authState.user;

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _profileCard(context, authState),
            const SizedBox(height: AppSpacing.lg),
            const Text('Trading', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            _settingsGroup(const [
              _SettingItem(
                Icons.currency_exchange,
                'Default Exchange',
                'Bybit',
              ),
              _SettingItem(Icons.speed, 'Risk Level', 'Moderate'),
              _SettingItem(Icons.attach_money, 'Base Currency', 'USDT'),
              _SettingItem(Icons.notifications_none, 'Trade Alerts', 'Enabled'),
            ]),
            const SizedBox(height: AppSpacing.lg),
            const Text('AI Assistant', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            _settingsGroup(const [
              _SettingItem(Icons.auto_awesome, 'AI Model', 'P-TRADER AI'),
              _SettingItem(
                Icons.tips_and_updates_outlined,
                'Auto Suggestions',
                'On',
              ),
              _SettingItem(Icons.mic_none, 'Voice Assistant', 'Coming Soon'),
            ]),
            const SizedBox(height: AppSpacing.lg),
            const Text('Security', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            _settingsGroup([
              const _SettingItem(Icons.fingerprint, 'Biometric Login', 'Off'),
              _SettingItem(
                Icons.password_outlined,
                'Change Password',
                'Update account password',
                onTap: user == null
                    ? null
                    : () {
                        Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => const ChangePasswordScreen(),
                          ),
                        );
                      },
              ),
              const _SettingItem(
                Icons.key_outlined,
                'API Keys',
                'Not Connected',
              ),
            ]),
            const SizedBox(height: AppSpacing.lg),
            const Text('About', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            _settingsGroup(const [
              _SettingItem(Icons.info_outline, 'Version', '1.0.0'),
              _SettingItem(Icons.privacy_tip_outlined, 'Privacy Policy', ''),
              _SettingItem(Icons.article_outlined, 'Terms of Service', ''),
            ]),
            const SizedBox(height: AppSpacing.lg),
            const Text('Danger Zone', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            _deactivateButton(context, ref, authState),
            const SizedBox(height: AppSpacing.md),
            _logoutButton(context, ref, authState),
            const SizedBox(height: AppSpacing.xl),
          ],
        ),
      ),
    );
  }

  Widget _profileCard(BuildContext context, AuthState authState) {
    final user = authState.user;

    return GestureDetector(
      onTap: user == null
          ? null
          : () {
              Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => EditProfileScreen(user: user),
                ),
              );
            },
      child: GlassCard(
        child: Row(
          children: [
            Container(
              height: 62,
              width: 62,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  colors: [AppColors.primary, Colors.deepPurpleAccent],
                ),
                borderRadius: BorderRadius.circular(22),
              ),
              child: const Icon(Icons.person, color: Colors.black, size: 34),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user?.fullName ?? 'P-TRADER AI User',
                    style: AppTextStyles.title,
                  ),
                  const SizedBox(height: AppSpacing.xs),
                  Text(
                    user?.email ?? 'Authenticated account',
                    style: AppTextStyles.body,
                  ),
                  if (user != null) ...[
                    const SizedBox(height: AppSpacing.xs),
                    const Text(
                      'Tap to edit profile',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ],
              ),
            ),
            if (user != null)
              const Icon(
                Icons.arrow_forward_ios,
                size: 16,
                color: AppColors.textSecondary,
              ),
          ],
        ),
      ),
    );
  }

  Widget _settingsGroup(List<_SettingItem> items) {
    return GlassCard(
      padding: EdgeInsets.zero,
      child: Column(
        children: items.asMap().entries.map((entry) {
          final index = entry.key;
          final item = entry.value;
          final isLast = index == items.length - 1;

          return Column(
            children: [
              ListTile(
                leading: CircleAvatar(
                  radius: 18,
                  backgroundColor: AppColors.primary.withValues(alpha: 0.13),
                  child: Icon(item.icon, color: AppColors.primary, size: 18),
                ),
                title: Text(
                  item.title,
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                subtitle: item.value.isEmpty
                    ? null
                    : Text(item.value, style: AppTextStyles.body),
                trailing: item.onTap == null
                    ? null
                    : const Icon(
                        Icons.arrow_forward_ios,
                        size: 14,
                        color: AppColors.textSecondary,
                      ),
                onTap: item.onTap,
              ),
              if (!isLast)
                const Divider(color: AppColors.divider, height: 1, indent: 72),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _deactivateButton(
    BuildContext context,
    WidgetRef ref,
    AuthState authState,
  ) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: !authState.isAuthenticated
            ? null
            : () => _confirmDeactivation(context, ref),
        icon: const Icon(Icons.person_off_outlined),
        label: const Text('Deactivate Account'),
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.danger,
          side: const BorderSide(color: AppColors.danger),
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
          ),
        ),
      ),
    );
  }

  Widget _logoutButton(
    BuildContext context,
    WidgetRef ref,
    AuthState authState,
  ) {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: authState.isLoading
            ? null
            : () => _confirmLogout(context, ref),
        icon: authState.isLoading
            ? const SizedBox(
                height: 18,
                width: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            : const Icon(Icons.logout),
        label: Text(authState.isLoading ? 'Logging out...' : 'Logout'),
        style: OutlinedButton.styleFrom(
          foregroundColor: AppColors.textSecondary,
          padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
          ),
        ),
      ),
    );
  }

  Future<void> _confirmDeactivation(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (_) => const _DeactivateAccountDialog(),
    );

    if (confirmed != true || !context.mounted) {
      return;
    }

    try {
      await ref.read(authProvider.notifier).deactivateAccount();

      if (!context.mounted) {
        return;
      }

      Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute<void>(builder: (_) => const LoginScreen()),
        (_) => false,
      );
    } on AppException catch (error) {
      if (context.mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.message)));
      }
    } catch (_) {
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Account deactivation failed.')),
        );
      }
    }
  }

  Future<void> _confirmLogout(BuildContext context, WidgetRef ref) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          title: const Text('Logout'),
          content: const Text(
            'Are you sure you want to end '
            'this secure session?',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(dialogContext).pop(false);
              },
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.of(dialogContext).pop(true);
              },
              child: const Text('Logout'),
            ),
          ],
        );
      },
    );

    if (confirmed != true || !context.mounted) {
      return;
    }

    final success = await ref.read(authProvider.notifier).logout();

    if (!context.mounted) {
      return;
    }

    if (!success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Logout failed. Please try again.')),
      );
      return;
    }

    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute<void>(builder: (_) => const LoginScreen()),
      (_) => false,
    );
  }
}

class _SettingItem {
  const _SettingItem(this.icon, this.title, this.value, {this.onTap});

  final IconData icon;
  final String title;
  final String value;
  final VoidCallback? onTap;
}

class _DeactivateAccountDialog extends StatefulWidget {
  const _DeactivateAccountDialog();

  @override
  State<_DeactivateAccountDialog> createState() =>
      _DeactivateAccountDialogState();
}

class _DeactivateAccountDialogState extends State<_DeactivateAccountDialog> {
  final _controller = TextEditingController();

  bool get _confirmed => _controller.text.trim() == 'DEACTIVATE';

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Deactivate Account'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'This disables your account and ends '
            'the current session.',
          ),
          const SizedBox(height: AppSpacing.md),
          const Text(
            'Type DEACTIVATE to continue.',
            style: TextStyle(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: AppSpacing.sm),
          TextField(
            controller: _controller,
            autocorrect: false,
            onChanged: (_) => setState(() {}),
            decoration: const InputDecoration(
              hintText: 'DEACTIVATE',
              border: OutlineInputBorder(),
            ),
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () {
            Navigator.of(context).pop(false);
          },
          child: const Text('Cancel'),
        ),
        FilledButton(
          onPressed: _confirmed
              ? () {
                  Navigator.of(context).pop(true);
                }
              : null,
          style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
          child: const Text('Deactivate'),
        ),
      ],
    );
  }
}
