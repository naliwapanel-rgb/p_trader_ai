import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import 'data/exchange_account.dart';
import 'providers/exchange_account_provider.dart';

class ExchangeAccountFormScreen extends ConsumerStatefulWidget {
  const ExchangeAccountFormScreen({super.key, this.account});

  final ExchangeAccount? account;

  bool get isEditing => account != null;

  @override
  ConsumerState<ExchangeAccountFormScreen> createState() =>
      _ExchangeAccountFormScreenState();
}

class _ExchangeAccountFormScreenState
    extends ConsumerState<ExchangeAccountFormScreen> {
  final _formKey = GlobalKey<FormState>();
  final _accountNameController = TextEditingController();
  final _apiKeyController = TextEditingController();
  final _apiSecretController = TextEditingController();

  String _exchangeName = 'BYBIT';
  bool _isTestnet = false;
  bool _isActive = true;
  bool _showApiKey = false;
  bool _showApiSecret = false;
  bool _saving = false;

  static const _exchanges = <String, String>{
    'BYBIT': 'Bybit',
    'BINANCE': 'Binance',
    'MEXC': 'MEXC',
    'GATEIO': 'Gate.io',
  };

  @override
  void initState() {
    super.initState();

    final account = widget.account;

    if (account != null) {
      _exchangeName = account.exchangeName.toUpperCase();
      _accountNameController.text = account.accountName;
      _isTestnet = account.isTestnet;
      _isActive = account.isActive;
    }
  }

  @override
  void dispose() {
    _accountNameController.dispose();
    _apiKeyController.dispose();
    _apiSecretController.dispose();
    super.dispose();
  }

  String? _validateAccountName(String? value) {
    final normalized = value?.trim() ?? '';

    if (normalized.length < 2) {
      return 'Enter an account name with at least 2 characters.';
    }

    if (normalized.length > 150) {
      return 'The account name is too long.';
    }

    return null;
  }

  String? _validateApiKey(String? value) {
    final normalized = value?.trim() ?? '';

    if (!widget.isEditing && normalized.length < 5) {
      return 'Enter a valid API key.';
    }

    if (normalized.isNotEmpty && normalized.length < 5) {
      return 'The API key must have at least 5 characters.';
    }

    return null;
  }

  String? _validateApiSecret(String? value) {
    final normalized = value?.trim() ?? '';

    if (!widget.isEditing && normalized.length < 5) {
      return 'Enter a valid API secret.';
    }

    if (normalized.isNotEmpty && normalized.length < 5) {
      return 'The API secret must have at least 5 characters.';
    }

    return null;
  }

  Future<void> _save() async {
    if (_saving || !_formKey.currentState!.validate()) {
      return;
    }

    final apiKey = _apiKeyController.text.trim();
    final apiSecret = _apiSecretController.text.trim();

    if (widget.isEditing &&
        ((apiKey.isEmpty && apiSecret.isNotEmpty) ||
            (apiKey.isNotEmpty && apiSecret.isEmpty))) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text(
            'Enter both the API key and API secret '
            'to replace the stored credentials.',
          ),
        ),
      );
      return;
    }

    setState(() => _saving = true);

    final notifier = ref.read(exchangeAccountProvider.notifier);

    ExchangeAccount? savedAccount;

    if (widget.account == null) {
      savedAccount = await notifier.createAccount(
        exchangeName: _exchangeName,
        accountName: _accountNameController.text.trim(),
        apiKey: apiKey,
        apiSecret: apiSecret,
        isTestnet: _isTestnet,
      );
    } else {
      savedAccount = await notifier.updateAccount(
        accountId: widget.account!.id,
        accountName: _accountNameController.text.trim(),
        apiKey: apiKey.isEmpty ? null : apiKey,
        apiSecret: apiSecret.isEmpty ? null : apiSecret,
        isTestnet: _isTestnet,
        isActive: _isActive,
      );
    }

    _apiKeyController.clear();
    _apiSecretController.clear();

    if (!mounted) {
      return;
    }

    setState(() => _saving = false);

    if (savedAccount == null) {
      final message =
          ref.read(exchangeAccountProvider).errorMessage ??
          'The exchange account could not be saved.';

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));
      return;
    }

    Navigator.of(context).pop(true);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.isEditing ? 'Edit Exchange Account' : 'Connect Exchange',
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.isEditing
                      ? 'Update the connection settings. '
                            'Stored credentials are never displayed.'
                      : 'Enter read-only API credentials from '
                            'your exchange account.',
                  style: AppTextStyles.body,
                ),
                const SizedBox(height: AppSpacing.lg),
                DropdownButtonFormField<String>(
                  initialValue: _exchangeName,
                  decoration: const InputDecoration(
                    labelText: 'Exchange',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.currency_exchange),
                  ),
                  items: _exchanges.entries
                      .map(
                        (entry) => DropdownMenuItem(
                          value: entry.key,
                          child: Text(entry.value),
                        ),
                      )
                      .toList(growable: false),
                  onChanged: widget.isEditing
                      ? null
                      : (value) {
                          if (value != null) {
                            setState(() => _exchangeName = value);
                          }
                        },
                ),
                const SizedBox(height: AppSpacing.md),
                TextFormField(
                  controller: _accountNameController,
                  validator: _validateAccountName,
                  textInputAction: TextInputAction.next,
                  decoration: const InputDecoration(
                    labelText: 'Account name',
                    hintText: 'My Bybit Read Only',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.badge_outlined),
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                TextFormField(
                  controller: _apiKeyController,
                  validator: _validateApiKey,
                  obscureText: !_showApiKey,
                  autocorrect: false,
                  enableSuggestions: false,
                  textInputAction: TextInputAction.next,
                  decoration: InputDecoration(
                    labelText: widget.isEditing
                        ? 'New API key — optional'
                        : 'API key',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.key_outlined),
                    suffixIcon: IconButton(
                      onPressed: () {
                        setState(() => _showApiKey = !_showApiKey);
                      },
                      icon: Icon(
                        _showApiKey ? Icons.visibility_off : Icons.visibility,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.md),
                TextFormField(
                  controller: _apiSecretController,
                  validator: _validateApiSecret,
                  obscureText: !_showApiSecret,
                  autocorrect: false,
                  enableSuggestions: false,
                  onFieldSubmitted: (_) => _save(),
                  decoration: InputDecoration(
                    labelText: widget.isEditing
                        ? 'New API secret — optional'
                        : 'API secret',
                    border: const OutlineInputBorder(),
                    prefixIcon: const Icon(Icons.password_outlined),
                    suffixIcon: IconButton(
                      onPressed: () {
                        setState(() => _showApiSecret = !_showApiSecret);
                      },
                      icon: Icon(
                        _showApiSecret
                            ? Icons.visibility_off
                            : Icons.visibility,
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: AppSpacing.sm),
                const Text(
                  'Credentials are sent only to the '
                  'P-TRADER AI backend and are stored encrypted.',
                  style: TextStyle(fontSize: 12),
                ),
                const SizedBox(height: AppSpacing.md),
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Use testnet'),
                  subtitle: const Text(
                    'Enable only when these credentials '
                    'belong to an exchange test environment.',
                  ),
                  value: _isTestnet,
                  onChanged: (value) {
                    setState(() => _isTestnet = value);
                  },
                ),
                if (widget.isEditing)
                  SwitchListTile.adaptive(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('Connection active'),
                    subtitle: const Text(
                      'Inactive accounts cannot be used '
                      'for balance synchronization or trading.',
                    ),
                    value: _isActive,
                    onChanged: (value) {
                      setState(() => _isActive = value);
                    },
                  ),
                const SizedBox(height: AppSpacing.lg),
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: _saving ? null : _save,
                    icon: _saving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.save_outlined),
                    label: Text(
                      _saving
                          ? 'Saving...'
                          : widget.isEditing
                          ? 'Save Changes'
                          : 'Connect Exchange',
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
