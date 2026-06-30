import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _profileCard(),
            const SizedBox(height: AppSpacing.lg),

            const Text('Trading', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            _settingsGroup([
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
            _settingsGroup([
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
              _SettingItem(Icons.fingerprint, 'Biometric Login', 'Off'),
              _SettingItem(Icons.lock_outline, 'Change PIN', ''),
              _SettingItem(Icons.key_outlined, 'API Keys', 'Not Connected'),
            ]),

            const SizedBox(height: AppSpacing.lg),
            const Text('About', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            _settingsGroup([
              _SettingItem(Icons.info_outline, 'Version', '1.0.0'),
              _SettingItem(Icons.privacy_tip_outlined, 'Privacy Policy', ''),
              _SettingItem(Icons.article_outlined, 'Terms of Service', ''),
            ]),

            const SizedBox(height: AppSpacing.lg),
            _logoutButton(),
            const SizedBox(height: AppSpacing.xl),
          ],
        ),
      ),
    );
  }

  Widget _profileCard() {
    return GlassCard(
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
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Innocent', style: AppTextStyles.title),
                SizedBox(height: AppSpacing.xs),
                Text('P-TRADER AI User', style: AppTextStyles.body),
              ],
            ),
          ),
          const Icon(
            Icons.arrow_forward_ios,
            size: 16,
            color: AppColors.textSecondary,
          ),
        ],
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
                trailing: const Icon(
                  Icons.arrow_forward_ios,
                  size: 14,
                  color: AppColors.textSecondary,
                ),
                onTap: () {},
              ),
              if (!isLast)
                const Divider(color: AppColors.divider, height: 1, indent: 72),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _logoutButton() {
    return SizedBox(
      width: double.infinity,
      child: OutlinedButton.icon(
        onPressed: () {},
        icon: const Icon(Icons.logout),
        label: const Text('Logout'),
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
}

class _SettingItem {
  final IconData icon;
  final String title;
  final String value;

  const _SettingItem(this.icon, this.title, this.value);
}
