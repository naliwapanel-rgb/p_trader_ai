import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import 'data/exchange_account.dart';
import 'data/exchange_balance.dart';
import 'exchange_account_form_screen.dart';
import 'providers/exchange_account_provider.dart';
import 'providers/exchange_account_state.dart';

class ExchangeAccountsScreen extends ConsumerStatefulWidget {
  const ExchangeAccountsScreen({super.key});

  @override
  ConsumerState<ExchangeAccountsScreen> createState() =>
      _ExchangeAccountsScreenState();
}

class _ExchangeAccountsScreenState
    extends ConsumerState<ExchangeAccountsScreen> {
  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      ref.read(exchangeAccountProvider.notifier).loadAccounts();
    });
  }

  Future<void> _openForm({ExchangeAccount? account}) async {
    await Navigator.of(context).push<bool>(
      MaterialPageRoute<bool>(
        builder: (_) => ExchangeAccountFormScreen(account: account),
      ),
    );
  }

  Future<void> _testConnection(ExchangeAccount account) async {
    final result = await ref
        .read(exchangeAccountProvider.notifier)
        .testConnection(account.id);

    if (!mounted) {
      return;
    }

    if (result == null) {
      _showError();
      return;
    }

    await showDialog<void>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: Text('${account.displayExchange} Connection'),
          content: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                result.appearsConnected
                    ? Icons.check_circle_outline
                    : Icons.error_outline,
                color: result.appearsConnected
                    ? AppColors.success
                    : AppColors.danger,
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(child: Text(result.summary)),
            ],
          ),
          actions: [
            FilledButton(
              onPressed: () {
                Navigator.of(context).pop();
              },
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _loadBalance(ExchangeAccount account) async {
    final balance = await ref
        .read(exchangeAccountProvider.notifier)
        .getBalance(account.id);

    if (!mounted) {
      return;
    }

    if (balance == null) {
      _showError();
      return;
    }

    await showDialog<void>(
      context: context,
      builder: (context) {
        return _BalanceDialog(account: account, balance: balance);
      },
    );
  }

  Future<void> _deleteAccount(ExchangeAccount account) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Delete Exchange Account'),
          content: Text(
            'Delete "${account.accountName}"? '
            'This removes its encrypted credentials '
            'from P-TRADER AI.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(false);
              },
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () {
                Navigator.of(context).pop(true);
              },
              style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
              child: const Text('Delete'),
            ),
          ],
        );
      },
    );

    if (confirmed != true) {
      return;
    }

    final deleted = await ref
        .read(exchangeAccountProvider.notifier)
        .deleteAccount(account.id);

    if (!mounted) {
      return;
    }

    if (!deleted) {
      _showError();
      return;
    }

    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Exchange account deleted.')));
  }

  void _showError() {
    final message =
        ref.read(exchangeAccountProvider).errorMessage ??
        'The exchange operation failed.';

    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(exchangeAccountProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Exchange Accounts'),
        actions: [
          IconButton(
            onPressed: state.isMutating ? null : () => _openForm(),
            icon: const Icon(Icons.add_circle_outline),
            tooltip: 'Connect exchange',
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () =>
            ref.read(exchangeAccountProvider.notifier).loadAccounts(),
        child: _body(state),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: state.isMutating ? null : () => _openForm(),
        icon: const Icon(Icons.add),
        label: const Text('Connect'),
      ),
    );
  }

  Widget _body(ExchangeAccountState state) {
    if (state.isLoading && state.accounts.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }

    if (state.errorMessage != null && state.accounts.isEmpty) {
      return ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          const SizedBox(height: 100),
          const Icon(Icons.cloud_off_outlined, size: 64),
          const SizedBox(height: AppSpacing.md),
          Text(
            state.errorMessage.toString(),
            textAlign: TextAlign.center,
            style: AppTextStyles.body,
          ),
          const SizedBox(height: AppSpacing.md),
          FilledButton(
            onPressed: () {
              ref.read(exchangeAccountProvider.notifier).loadAccounts();
            },
            child: const Text('Try Again'),
          ),
        ],
      );
    }

    if (state.accounts.isEmpty) {
      return ListView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          const SizedBox(height: 90),
          const Icon(Icons.currency_exchange, size: 72),
          const SizedBox(height: AppSpacing.md),
          Text(
            'No exchange accounts connected',
            textAlign: TextAlign.center,
            style: AppTextStyles.title,
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Connect a read-only API account to '
            'test credentials and retrieve balances.',
            textAlign: TextAlign.center,
            style: AppTextStyles.body,
          ),
          const SizedBox(height: AppSpacing.lg),
          FilledButton.icon(
            onPressed: () => _openForm(),
            icon: const Icon(Icons.add_link),
            label: const Text('Connect Exchange'),
          ),
        ],
      );
    }

    return ListView.separated(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.md,
        AppSpacing.md,
        AppSpacing.md,
        100,
      ),
      itemCount: state.accounts.length,
      separatorBuilder: (_, _) => const SizedBox(height: AppSpacing.sm),
      itemBuilder: (context, index) {
        final account = state.accounts[index];

        return _accountCard(account, state.isMutating);
      },
    );
  }

  Widget _accountCard(ExchangeAccount account, bool busy) {
    final statusColor = account.isActive
        ? AppColors.success
        : AppColors.textSecondary;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CircleAvatar(
                  child: Text(account.displayExchange.substring(0, 1)),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(account.accountName, style: AppTextStyles.title),
                      Text(account.displayExchange, style: AppTextStyles.body),
                    ],
                  ),
                ),
                PopupMenuButton<String>(
                  enabled: !busy,
                  onSelected: (action) {
                    switch (action) {
                      case 'test':
                        _testConnection(account);
                        break;
                      case 'balance':
                        _loadBalance(account);
                        break;
                      case 'edit':
                        _openForm(account: account);
                        break;
                      case 'delete':
                        _deleteAccount(account);
                        break;
                    }
                  },
                  itemBuilder: (_) => const [
                    PopupMenuItem(
                      value: 'test',
                      child: ListTile(
                        leading: Icon(Icons.wifi_tethering),
                        title: Text('Test Connection'),
                      ),
                    ),
                    PopupMenuItem(
                      value: 'balance',
                      child: ListTile(
                        leading: Icon(Icons.account_balance_wallet_outlined),
                        title: Text('View Balance'),
                      ),
                    ),
                    PopupMenuItem(
                      value: 'edit',
                      child: ListTile(
                        leading: Icon(Icons.edit_outlined),
                        title: Text('Edit'),
                      ),
                    ),
                    PopupMenuItem(
                      value: 'delete',
                      child: ListTile(
                        leading: Icon(Icons.delete_outline),
                        title: Text('Delete'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Wrap(
              spacing: AppSpacing.sm,
              runSpacing: AppSpacing.sm,
              children: [
                Chip(
                  avatar: Icon(
                    account.isActive ? Icons.check_circle : Icons.pause_circle,
                    size: 18,
                    color: statusColor,
                  ),
                  label: Text(account.isActive ? 'Active' : 'Inactive'),
                ),
                Chip(
                  avatar: const Icon(Icons.public, size: 18),
                  label: Text(account.isTestnet ? 'Testnet' : 'Mainnet'),
                ),
                const Chip(
                  avatar: Icon(Icons.lock_outline, size: 18),
                  label: Text('Credentials encrypted'),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: busy ? null : () => _testConnection(account),
                    icon: const Icon(Icons.wifi_tethering),
                    label: const Text('Test'),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: busy ? null : () => _loadBalance(account),
                    icon: const Icon(Icons.account_balance_wallet_outlined),
                    label: const Text('Balance'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _BalanceDialog extends StatelessWidget {
  const _BalanceDialog({required this.account, required this.balance});

  final ExchangeAccount account;
  final ExchangeBalance balance;

  @override
  Widget build(BuildContext context) {
    final visibleCoins = balance.coins.take(8).toList();

    return AlertDialog(
      title: Text('${account.displayExchange} Balance'),
      content: SizedBox(
        width: 460,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(account.accountName, style: AppTextStyles.title),
              Text(
                'Account type: ${balance.accountType}',
                style: AppTextStyles.body,
              ),
              const SizedBox(height: AppSpacing.md),
              _valueRow('Total equity', balance.totalEquityUsd),
              _valueRow('Wallet balance', balance.totalWalletBalanceUsd),
              _valueRow('Available balance', balance.totalAvailableBalanceUsd),
              _valueRow('Unrealized P/L', balance.totalUnrealizedPnlUsd),
              if (visibleCoins.isNotEmpty) ...[
                const Divider(height: AppSpacing.xl),
                Text('Assets', style: AppTextStyles.title),
                const SizedBox(height: AppSpacing.sm),
                for (final coin in visibleCoins)
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    title: Text(coin.symbol),
                    subtitle: Text(
                      'Available: '
                      '${coin.availableBalance}',
                    ),
                    trailing: Text(coin.walletBalance.toStringAsFixed(8)),
                  ),
              ],
            ],
          ),
        ),
      ),
      actions: [
        FilledButton(
          onPressed: () {
            Navigator.of(context).pop();
          },
          child: const Text('Close'),
        ),
      ],
    );
  }

  Widget _valueRow(String label, double value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        children: [
          Expanded(child: Text(label, style: AppTextStyles.body)),
          Text(
            '\$${value.toStringAsFixed(2)}',
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
