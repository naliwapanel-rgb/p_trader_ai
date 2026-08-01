import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/errors/app_exception.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../auth/providers/auth_provider.dart';

class ChangePasswordScreen extends ConsumerStatefulWidget {
  const ChangePasswordScreen({super.key});

  @override
  ConsumerState<ChangePasswordScreen> createState() =>
      _ChangePasswordScreenState();
}

class _ChangePasswordScreenState extends ConsumerState<ChangePasswordScreen> {
  final _formKey = GlobalKey<FormState>();

  final _currentPasswordController = TextEditingController();

  final _newPasswordController = TextEditingController();

  final _confirmationController = TextEditingController();

  bool _isSaving = false;
  bool _hideCurrentPassword = true;
  bool _hideNewPassword = true;
  bool _hideConfirmation = true;
  String? _errorMessage;

  @override
  void dispose() {
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmationController.dispose();
    super.dispose();
  }

  Future<void> _changePassword() async {
    if (_isSaving || !_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isSaving = true;
      _errorMessage = null;
    });

    try {
      await ref
          .read(authProvider.notifier)
          .updatePassword(
            currentPassword: _currentPasswordController.text,
            newPassword: _newPasswordController.text,
          );

      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password updated successfully.')),
      );

      Navigator.of(context).pop();
    } on AppException catch (error) {
      if (mounted) {
        setState(() {
          _errorMessage = error.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _errorMessage = 'Password update failed unexpectedly.';
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Change Password')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Protect your account', style: AppTextStyles.title),
              const SizedBox(height: AppSpacing.sm),
              const Text(
                'Use at least 8 characters. Your new '
                'password must differ from the current one.',
                style: AppTextStyles.body,
              ),
              const SizedBox(height: AppSpacing.lg),
              if (_errorMessage != null) ...[
                _PasswordErrorPanel(message: _errorMessage!),
                const SizedBox(height: AppSpacing.md),
              ],
              _passwordField(
                controller: _currentPasswordController,
                label: 'Current password',
                hidden: _hideCurrentPassword,
                onToggle: () {
                  setState(() {
                    _hideCurrentPassword = !_hideCurrentPassword;
                  });
                },
                validator: _validatePassword,
                action: TextInputAction.next,
              ),
              const SizedBox(height: AppSpacing.md),
              _passwordField(
                controller: _newPasswordController,
                label: 'New password',
                hidden: _hideNewPassword,
                onToggle: () {
                  setState(() {
                    _hideNewPassword = !_hideNewPassword;
                  });
                },
                validator: _validateNewPassword,
                action: TextInputAction.next,
              ),
              const SizedBox(height: AppSpacing.md),
              _passwordField(
                controller: _confirmationController,
                label: 'Confirm new password',
                hidden: _hideConfirmation,
                onToggle: () {
                  setState(() {
                    _hideConfirmation = !_hideConfirmation;
                  });
                },
                validator: _validateConfirmation,
                action: TextInputAction.done,
                onSubmitted: (_) => _changePassword(),
              ),
              const SizedBox(height: AppSpacing.xl),
              FilledButton.icon(
                onPressed: _isSaving ? null : _changePassword,
                icon: _isSaving
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.lock_reset),
                label: Text(_isSaving ? 'Updating...' : 'Update password'),
                style: FilledButton.styleFrom(
                  backgroundColor: AppColors.primary,
                  foregroundColor: Colors.black,
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _passwordField({
    required TextEditingController controller,
    required String label,
    required bool hidden,
    required VoidCallback onToggle,
    required String? Function(String?) validator,
    required TextInputAction action,
    ValueChanged<String>? onSubmitted,
  }) {
    return TextFormField(
      controller: controller,
      enabled: !_isSaving,
      obscureText: hidden,
      textInputAction: action,
      validator: validator,
      onFieldSubmitted: onSubmitted,
      autocorrect: false,
      enableSuggestions: false,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: const Icon(
          Icons.password_outlined,
          color: AppColors.primary,
        ),
        suffixIcon: IconButton(
          onPressed: onToggle,
          icon: Icon(
            hidden ? Icons.visibility_outlined : Icons.visibility_off_outlined,
          ),
        ),
        filled: true,
        fillColor: AppColors.card,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(AppSpacing.radius),
        ),
      ),
    );
  }

  String? _validatePassword(String? value) {
    final password = value ?? '';

    if (password.isEmpty) {
      return 'Enter your current password.';
    }

    if (password.length < 8) {
      return 'Password must contain at least 8 characters.';
    }

    if (password.length > 72) {
      return 'Password cannot exceed 72 characters.';
    }

    return null;
  }

  String? _validateNewPassword(String? value) {
    final validation = _validatePassword(value);

    if (validation != null) {
      return validation.replaceFirst('current password', 'new password');
    }

    if (value == _currentPasswordController.text) {
      return 'New password must differ from the current password.';
    }

    return null;
  }

  String? _validateConfirmation(String? value) {
    if (value == null || value.isEmpty) {
      return 'Confirm your new password.';
    }

    if (value != _newPasswordController.text) {
      return 'Passwords do not match.';
    }

    return null;
  }
}

class _PasswordErrorPanel extends StatelessWidget {
  const _PasswordErrorPanel({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.danger.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(AppSpacing.radius),
        border: Border.all(color: AppColors.danger.withValues(alpha: 0.45)),
      ),
      child: Text(message, style: const TextStyle(color: AppColors.danger)),
    );
  }
}
