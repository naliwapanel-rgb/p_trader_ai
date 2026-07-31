import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/primary_button.dart';
import '../../navigation/main_navigation.dart';
import 'providers/auth_provider.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool rememberMe = true;
  bool hidePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _submitLogin() async {
    final authState = ref.read(authProvider);

    if (authState.isLoading) {
      return;
    }

    FocusScope.of(context).unfocus();
    ref.read(authProvider.notifier).clearError();

    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    final success = await ref
        .read(authProvider.notifier)
        .login(
          email: _emailController.text,
          password: _passwordController.text,
          rememberMe: rememberMe,
        );

    if (!mounted || !success) {
      return;
    }

    Navigator.pushReplacement(
      context,
      MaterialPageRoute<void>(builder: (_) => const MainNavigation()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(AppSpacing.lg),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 430),
              child: AutofillGroup(
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      _logo(),
                      const SizedBox(height: AppSpacing.xl),
                      _inputField(
                        controller: _emailController,
                        label: 'Email',
                        hint: 'Enter your email',
                        icon: Icons.email_outlined,
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.next,
                        autofillHints: const <String>[
                          AutofillHints.email,
                          AutofillHints.username,
                        ],
                        enabled: !authState.isLoading,
                        validator: _validateEmail,
                      ),
                      const SizedBox(height: AppSpacing.md),
                      _inputField(
                        controller: _passwordController,
                        label: 'Password',
                        hint: 'Enter your password',
                        icon: Icons.lock_outline,
                        obscureText: hidePassword,
                        textInputAction: TextInputAction.done,
                        autofillHints: const <String>[AutofillHints.password],
                        enabled: !authState.isLoading,
                        validator: _validatePassword,
                        onFieldSubmitted: (_) => _submitLogin(),
                        suffix: IconButton(
                          onPressed: authState.isLoading
                              ? null
                              : () {
                                  setState(() => hidePassword = !hidePassword);
                                },
                          icon: Icon(
                            hidePassword
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                          ),
                        ),
                      ),
                      const SizedBox(height: AppSpacing.sm),
                      Row(
                        children: [
                          Checkbox(
                            value: rememberMe,
                            activeColor: AppColors.primary,
                            onChanged: authState.isLoading
                                ? null
                                : (value) {
                                    setState(() => rememberMe = value ?? false);
                                  },
                          ),
                          const Text('Remember me', style: AppTextStyles.body),
                          const Spacer(),
                          TextButton(
                            onPressed: authState.isLoading ? null : () {},
                            child: const Text('Forgot Password?'),
                          ),
                        ],
                      ),
                      if (authState.errorMessage != null) ...[
                        const SizedBox(height: AppSpacing.sm),
                        Container(
                          padding: const EdgeInsets.all(AppSpacing.md),
                          decoration: BoxDecoration(
                            color: Colors.redAccent.withValues(alpha: 0.10),
                            borderRadius: BorderRadius.circular(
                              AppSpacing.radius,
                            ),
                            border: Border.all(
                              color: Colors.redAccent.withValues(alpha: 0.45),
                            ),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(
                                Icons.error_outline,
                                color: Colors.redAccent,
                              ),
                              const SizedBox(width: AppSpacing.sm),
                              Expanded(
                                child: Text(
                                  authState.errorMessage!,
                                  style: AppTextStyles.body.copyWith(
                                    color: Colors.redAccent,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: AppSpacing.md),
                      PrimaryButton(
                        label: authState.isLoading ? 'Signing in...' : 'Login',
                        onPressed: _submitLogin,
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Row(
                        children: [
                          const Expanded(
                            child: Divider(color: AppColors.divider),
                          ),
                          Padding(
                            padding: const EdgeInsets.symmetric(
                              horizontal: AppSpacing.md,
                            ),
                            child: Text(
                              'OR',
                              style: AppTextStyles.body.copyWith(fontSize: 12),
                            ),
                          ),
                          const Expanded(
                            child: Divider(color: AppColors.divider),
                          ),
                        ],
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      OutlinedButton.icon(
                        onPressed: authState.isLoading ? null : () {},
                        icon: const Icon(Icons.g_mobiledata, size: 28),
                        label: const Text('Continue with Google'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: AppColors.textPrimary,
                          side: const BorderSide(color: AppColors.divider),
                          padding: const EdgeInsets.symmetric(
                            vertical: AppSpacing.md,
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(
                              AppSpacing.radius,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: AppSpacing.lg),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Text(
                            "Don't have an account?",
                            style: AppTextStyles.body,
                          ),
                          TextButton(
                            onPressed: authState.isLoading ? null : () {},
                            child: const Text('Create Account'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  String? _validateEmail(String? value) {
    final email = value?.trim() ?? '';

    if (email.isEmpty) {
      return 'Enter your email address.';
    }

    final emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');

    if (!emailPattern.hasMatch(email)) {
      return 'Enter a valid email address.';
    }

    return null;
  }

  String? _validatePassword(String? value) {
    final password = value ?? '';

    if (password.isEmpty) {
      return 'Enter your password.';
    }

    if (password.length < 8) {
      return 'Password must contain at least 8 characters.';
    }

    if (password.length > 72) {
      return 'Password cannot exceed 72 characters.';
    }

    return null;
  }

  Widget _logo() {
    return Column(
      children: [
        Container(
          height: 110,
          width: 110,
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.card,
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: AppColors.primary.withValues(alpha: 0.4)),
          ),
          child: Image.asset(
            'assets/images/logo/app_icon.png',
            fit: BoxFit.contain,
          ),
        ),
        const SizedBox(height: AppSpacing.lg),
        const Text('P-TRADER AI', style: AppTextStyles.heading),
        const SizedBox(height: AppSpacing.sm),
        const Text(
          'Professional Crypto Trading Platform',
          textAlign: TextAlign.center,
          style: AppTextStyles.body,
        ),
      ],
    );
  }

  Widget _inputField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    required bool enabled,
    required String? Function(String?) validator,
    bool obscureText = false,
    Widget? suffix,
    TextInputType? keyboardType,
    TextInputAction? textInputAction,
    Iterable<String>? autofillHints,
    ValueChanged<String>? onFieldSubmitted,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: AppTextStyles.body),
        const SizedBox(height: AppSpacing.sm),
        TextFormField(
          controller: controller,
          enabled: enabled,
          obscureText: obscureText,
          keyboardType: keyboardType,
          textInputAction: textInputAction,
          autofillHints: autofillHints,
          onFieldSubmitted: onFieldSubmitted,
          validator: validator,
          autocorrect: false,
          enableSuggestions: !obscureText,
          style: const TextStyle(color: AppColors.textPrimary),
          decoration: InputDecoration(
            hintText: hint,
            hintStyle: const TextStyle(color: AppColors.textSecondary),
            prefixIcon: Icon(icon, color: AppColors.primary),
            suffixIcon: suffix,
            filled: true,
            fillColor: AppColors.card,
            contentPadding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.md,
              vertical: AppSpacing.md,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radius),
              borderSide: const BorderSide(color: AppColors.divider),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radius),
              borderSide: const BorderSide(color: AppColors.divider),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radius),
              borderSide: const BorderSide(color: AppColors.primary),
            ),
            errorBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(AppSpacing.radius),
              borderSide: const BorderSide(color: Colors.redAccent),
            ),
          ),
        ),
      ],
    );
  }
}
