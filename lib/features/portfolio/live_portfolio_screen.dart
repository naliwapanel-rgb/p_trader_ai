import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/app_card.dart';
import '../../core/widgets/coin_logo.dart';
import '../../core/widgets/section_title.dart';
import '../exchange_accounts/data/exchange_account.dart';
import '../exchange_accounts/providers/exchange_account_provider.dart';
import 'data/backend_portfolio.dart';
import 'data/portfolio_sync_coin.dart';
import 'data/portfolio_sync_snapshot.dart';
import 'providers/live_portfolio_provider.dart';
import 'providers/live_portfolio_state.dart';

class LivePortfolioScreen extends ConsumerStatefulWidget {
  const LivePortfolioScreen({super.key});

  @override
  ConsumerState<LivePortfolioScreen> createState() {
    return _LivePortfolioScreenState();
  }
}

class _LivePortfolioScreenState extends ConsumerState<LivePortfolioScreen> {
  bool _isInitializing = true;
  bool _isRefreshing = false;

  int? _selectedExchangeAccountId;
  String _category = 'linear';
  String _settleCoin = 'USDT';

  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      _initialize();
    });
  }

  Future<void> _initialize() async {
    try {
      final startupTasks = <Future<void>>[];

      final exchangeState = ref.read(exchangeAccountProvider);

      final portfolioState = ref.read(livePortfolioProvider);

      if (exchangeState.accounts.isEmpty) {
        startupTasks.add(
          ref.read(exchangeAccountProvider.notifier).loadAccounts(),
        );
      }

      if (portfolioState.portfolios.isEmpty) {
        startupTasks.add(
          ref.read(livePortfolioProvider.notifier).loadPortfolios(),
        );
      }

      if (startupTasks.isNotEmpty) {
        await Future.wait(startupTasks);
      }

      if (!mounted) {
        return;
      }

      _ensureExchangeSelection();
      await _loadSelectedPortfolioDetails();
    } finally {
      if (mounted) {
        setState(() {
          _isInitializing = false;
        });
      }
    }
  }

  Future<void> _refresh() async {
    if (_isRefreshing) {
      return;
    }

    setState(() {
      _isRefreshing = true;
    });

    try {
      await Future.wait<void>([
        ref.read(exchangeAccountProvider.notifier).loadAccounts(),
        ref.read(livePortfolioProvider.notifier).loadPortfolios(),
      ]);

      if (!mounted) {
        return;
      }

      _ensureExchangeSelection();
      await _loadSelectedPortfolioDetails();
    } finally {
      if (mounted) {
        setState(() {
          _isRefreshing = false;
        });
      }
    }
  }

  void _ensureExchangeSelection() {
    final activeAccounts = ref
        .read(exchangeAccountProvider)
        .accounts
        .where((account) => account.isActive)
        .toList(growable: false);

    final currentSelectionExists = activeAccounts.any(
      (account) => account.id == _selectedExchangeAccountId,
    );

    if (currentSelectionExists) {
      return;
    }

    setState(() {
      _selectedExchangeAccountId = activeAccounts.isEmpty
          ? null
          : activeAccounts.first.id;
    });
  }

  Future<void> _loadSelectedPortfolioDetails() async {
    final state = ref.read(livePortfolioProvider);

    if (state.selectedPortfolioId == null) {
      return;
    }

    final notifier = ref.read(livePortfolioProvider.notifier);

    await notifier.loadLatestSnapshot(
      exchangeAccountId: _selectedExchangeAccountId,
    );

    await notifier.loadSyncHistory(limit: 20);
  }

  Future<void> _selectPortfolio(int portfolioId) async {
    ref.read(livePortfolioProvider.notifier).selectPortfolio(portfolioId);

    await _loadSelectedPortfolioDetails();
  }

  Future<void> _createPortfolio() async {
    final result = await showDialog<Map<String, String>>(
      context: context,
      useRootNavigator: false,
      builder: (_) {
        return const _CreateLivePortfolioDialog();
      },
    );

    if (result == null || !mounted) {
      return;
    }

    await ref
        .read(livePortfolioProvider.notifier)
        .createPortfolio(
          name: result['name']!,
          baseCurrency: result['base_currency']!,
        );
  }

  Future<void> _synchronize() async {
    final accountId = _selectedExchangeAccountId;

    if (accountId == null) {
      return;
    }

    // synchronize() already inserts the returned snapshot into
    // latestSnapshot and history. A second history request here
    // only delays the interface and duplicates backend work.
    await ref
        .read(livePortfolioProvider.notifier)
        .synchronize(
          exchangeAccountId: accountId,
          category: _category,
          settleCoin: _settleCoin,
        );
  }

  @override
  Widget build(BuildContext context) {
    final portfolioState = ref.watch(livePortfolioProvider);

    final exchangeState = ref.watch(exchangeAccountProvider);

    final activeAccounts = exchangeState.accounts
        .where((account) => account.isActive)
        .toList(growable: false);

    final isBusy =
        portfolioState.isLoading ||
        portfolioState.isMutating ||
        exchangeState.isLoading ||
        exchangeState.isMutating ||
        _isRefreshing;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Live Portfolio'),
        actions: [
          IconButton(
            tooltip: 'Refresh live portfolio',
            onPressed: isBusy ? null : _refresh,
            icon: _isRefreshing
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _isInitializing && portfolioState.portfolios.isEmpty
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.all(AppSpacing.md),
                children: [
                  _controlCard(
                    state: portfolioState,
                    activeAccounts: activeAccounts,
                    exchangeError: exchangeState.errorMessage,
                    isBusy: isBusy,
                  ),
                  if (portfolioState.errorMessage != null) ...[
                    const SizedBox(height: AppSpacing.md),
                    _messageCard(portfolioState.errorMessage!, isError: true),
                  ],
                  if (portfolioState.infoMessage != null) ...[
                    const SizedBox(height: AppSpacing.md),
                    _messageCard(portfolioState.infoMessage!, isError: false),
                  ],
                  const SizedBox(height: AppSpacing.lg),
                  ..._portfolioContent(
                    state: portfolioState,
                    activeAccounts: activeAccounts,
                  ),
                  const SizedBox(height: AppSpacing.lg),
                  const SectionTitle('Synchronization History'),
                  const SizedBox(height: AppSpacing.sm),
                  _historyCard(portfolioState.history),
                  const SizedBox(height: AppSpacing.xl),
                ],
              ),
            ),
    );
  }

  Widget _controlCard({
    required LivePortfolioState state,
    required List<ExchangeAccount> activeAccounts,
    required String? exchangeError,
    required bool isBusy,
  }) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.cloud_sync_outlined, color: AppColors.primary),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Text(
                  'Backend Portfolio Sync',
                  style: AppTextStyles.title,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Synchronize balances, positions and orders '
            'from an active exchange account.',
            style: AppTextStyles.body,
          ),
          if (state.portfolios.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.md),
            DropdownButtonFormField<int>(
              key: ValueKey<int?>(state.selectedPortfolioId),
              initialValue: state.selectedPortfolioId,
              decoration: const InputDecoration(
                labelText: 'Live portfolio',
                prefixIcon: Icon(Icons.pie_chart_outline),
              ),
              items: state.portfolios
                  .map(
                    (portfolio) => DropdownMenuItem<int>(
                      value: portfolio.id,
                      child: Text(
                        '${portfolio.name} '
                        '(${portfolio.baseCurrency})',
                      ),
                    ),
                  )
                  .toList(growable: false),
              onChanged: isBusy
                  ? null
                  : (portfolioId) {
                      if (portfolioId != null) {
                        _selectPortfolio(portfolioId);
                      }
                    },
            ),
          ],
          const SizedBox(height: AppSpacing.md),
          if (activeAccounts.isNotEmpty)
            DropdownButtonFormField<int>(
              key: ValueKey<int?>(_selectedExchangeAccountId),
              initialValue: _selectedExchangeAccountId,
              decoration: const InputDecoration(
                labelText: 'Exchange account',
                prefixIcon: Icon(Icons.currency_exchange),
              ),
              items: activeAccounts
                  .map(
                    (account) => DropdownMenuItem<int>(
                      value: account.id,
                      child: Text(
                        '${account.displayExchange} — '
                        '${account.accountName}',
                      ),
                    ),
                  )
                  .toList(growable: false),
              onChanged: isBusy
                  ? null
                  : (accountId) {
                      setState(() {
                        _selectedExchangeAccountId = accountId;
                      });
                    },
            )
          else
            _warningBox(
              exchangeError ??
                  'No active exchange account is '
                      'available. Add one from Settings.',
            ),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: ValueKey<String>(_category),
                  initialValue: _category,
                  decoration: const InputDecoration(labelText: 'Category'),
                  items: const [
                    DropdownMenuItem(value: 'linear', child: Text('Linear')),
                    DropdownMenuItem(value: 'inverse', child: Text('Inverse')),
                    DropdownMenuItem(value: 'option', child: Text('Options')),
                  ],
                  onChanged: isBusy
                      ? null
                      : (value) {
                          if (value != null) {
                            setState(() {
                              _category = value;
                            });
                          }
                        },
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: DropdownButtonFormField<String>(
                  key: ValueKey<String>(_settleCoin),
                  initialValue: _settleCoin,
                  decoration: const InputDecoration(labelText: 'Settle coin'),
                  items: const [
                    DropdownMenuItem(value: 'USDT', child: Text('USDT')),
                    DropdownMenuItem(value: 'USDC', child: Text('USDC')),
                    DropdownMenuItem(value: 'BTC', child: Text('BTC')),
                  ],
                  onChanged: isBusy
                      ? null
                      : (value) {
                          if (value != null) {
                            setState(() {
                              _settleCoin = value;
                            });
                          }
                        },
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Wrap(
            spacing: AppSpacing.sm,
            runSpacing: AppSpacing.sm,
            children: [
              FilledButton.icon(
                onPressed:
                    isBusy ||
                        state.selectedPortfolio == null ||
                        _selectedExchangeAccountId == null
                    ? null
                    : _synchronize,
                icon: state.isMutating
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.sync),
                label: const Text('Synchronize'),
              ),
              OutlinedButton.icon(
                onPressed: state.isMutating ? null : _createPortfolio,
                icon: const Icon(Icons.add_chart_outlined),
                label: Text(
                  state.portfolios.isEmpty
                      ? 'Create Live Portfolio'
                      : 'Create Another',
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<Widget> _portfolioContent({
    required LivePortfolioState state,
    required List<ExchangeAccount> activeAccounts,
  }) {
    final portfolio = state.selectedPortfolio;
    final snapshot = state.latestSnapshot;

    if (portfolio == null) {
      return <Widget>[
        _emptyCard(
          icon: Icons.cloud_off_outlined,
          title: 'No live portfolio yet',
          message:
              'Create your first backend portfolio '
              'before synchronizing an exchange account.',
        ),
      ];
    }

    if (snapshot == null) {
      return <Widget>[
        _portfolioHeader(portfolio),
        const SizedBox(height: AppSpacing.md),
        _emptyCard(
          icon: Icons.sync_problem_outlined,
          title: 'No synchronization snapshot',
          message: activeAccounts.isEmpty
              ? 'Connect an active exchange account '
                    'before synchronizing.'
              : 'Select an exchange account and press '
                    'Synchronize.',
        ),
      ];
    }

    return <Widget>[
      _portfolioHeader(portfolio),
      const SizedBox(height: AppSpacing.lg),
      const SectionTitle('Live Account Summary'),
      const SizedBox(height: AppSpacing.sm),
      _summaryCard(snapshot),
      const SizedBox(height: AppSpacing.lg),
      const SectionTitle('Live Assets'),
      const SizedBox(height: AppSpacing.sm),
      _assetList(snapshot.coins),
      const SizedBox(height: AppSpacing.lg),
      SectionTitle(
        'Open Positions '
        '(${snapshot.openPositionCount})',
      ),
      const SizedBox(height: AppSpacing.sm),
      _recordList(
        snapshot.positionsPayload,
        emptyMessage: 'No open positions.',
        icon: Icons.candlestick_chart_outlined,
      ),
      const SizedBox(height: AppSpacing.lg),
      SectionTitle('Open Orders (${snapshot.openOrderCount})'),
      const SizedBox(height: AppSpacing.sm),
      _recordList(
        snapshot.ordersPayload,
        emptyMessage: 'No open orders.',
        icon: Icons.receipt_long_outlined,
      ),
    ];
  }

  Widget _portfolioHeader(BackendPortfolio portfolio) {
    return AppCard(
      child: Row(
        children: [
          const Icon(
            Icons.account_balance_wallet_outlined,
            color: AppColors.primary,
            size: 34,
          ),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(portfolio.name, style: AppTextStyles.title),
                Text(
                  'Base currency: '
                  '${portfolio.baseCurrency}',
                  style: AppTextStyles.body,
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(_money(portfolio.totalValue), style: AppTextStyles.title),
              Text(
                _signedMoney(portfolio.profitLoss),
                style: TextStyle(
                  color: portfolio.profitLoss >= 0
                      ? AppColors.success
                      : AppColors.danger,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _summaryCard(PortfolioSyncSnapshot snapshot) {
    final statusColor = switch (snapshot.status) {
      'SUCCESS' => AppColors.success,
      'PARTIAL' => AppColors.warning,
      _ => AppColors.danger,
    };

    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: Text(
                  '${snapshot.exchangeName} '
                  '${snapshot.accountType}',
                  style: AppTextStyles.title,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(50),
                ),
                child: Text(
                  snapshot.status,
                  style: TextStyle(
                    color: statusColor,
                    fontWeight: FontWeight.bold,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.xs),
          Text(
            'Synchronized: '
            '${_formatDate(snapshot.syncedAt)}',
            style: AppTextStyles.body,
          ),
          const SizedBox(height: AppSpacing.md),
          Wrap(
            spacing: AppSpacing.sm,
            runSpacing: AppSpacing.sm,
            children: [
              _metric('Total Equity', _money(snapshot.totalEquityUsd)),
              _metric('Wallet Balance', _money(snapshot.totalWalletBalanceUsd)),
              _metric('Available', _money(snapshot.totalAvailableBalanceUsd)),
              _metric('Position Value', _money(snapshot.totalPositionValueUsd)),
              _metric(
                'Unrealized P/L',
                _signedMoney(snapshot.totalUnrealizedPnlUsd),
                valueColor: snapshot.totalUnrealizedPnlUsd >= 0
                    ? AppColors.success
                    : AppColors.danger,
              ),
              _metric(
                'Realized P/L',
                _signedMoney(snapshot.totalRealizedPnlUsd),
                valueColor: snapshot.totalRealizedPnlUsd >= 0
                    ? AppColors.success
                    : AppColors.danger,
              ),
            ],
          ),
          if (snapshot.errorMessage != null) ...[
            const SizedBox(height: AppSpacing.md),
            _warningBox(snapshot.errorMessage!),
          ],
        ],
      ),
    );
  }

  Widget _metric(String label, String value, {Color? valueColor}) {
    return Container(
      width: 150,
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: Theme.of(
          context,
        ).colorScheme.surfaceContainerHighest.withValues(alpha: 0.45),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.body.copyWith(fontSize: 12)),
          const SizedBox(height: 4),
          Text(
            value,
            style: AppTextStyles.title.copyWith(
              color: valueColor,
              fontSize: 15,
            ),
          ),
        ],
      ),
    );
  }

  Widget _assetList(List<PortfolioSyncCoin> coins) {
    final visibleCoins = coins
        .where(
          (coin) =>
              coin.equity != 0 ||
              coin.walletBalance != 0 ||
              coin.availableBalance != 0 ||
              coin.usdValue != 0,
        )
        .toList(growable: false);

    if (visibleCoins.isEmpty) {
      return _emptyCard(
        icon: Icons.account_balance_wallet_outlined,
        title: 'No non-zero balances',
        message:
            'The exchange returned no non-zero '
            'coin balances.',
      );
    }

    return Column(
      children: visibleCoins
          .map(
            (coin) => Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: AppCard(
                child: Row(
                  children: [
                    CoinLogo(symbol: coin.coin.toLowerCase()),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(coin.coin, style: AppTextStyles.title),
                          Text(
                            'Wallet: '
                            '${_amount(coin.walletBalance)}',
                            style: AppTextStyles.body,
                          ),
                          Text(
                            'Available: '
                            '${_amount(coin.availableBalance)}',
                            style: AppTextStyles.body,
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(_money(coin.usdValue), style: AppTextStyles.title),
                        Text(
                          'Locked: '
                          '${_amount(coin.lockedBalance)}',
                          style: AppTextStyles.body.copyWith(fontSize: 11),
                        ),
                        Text(
                          _signedMoney(coin.unrealizedPnl),
                          style: TextStyle(
                            color: coin.unrealizedPnl >= 0
                                ? AppColors.success
                                : AppColors.danger,
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
          )
          .toList(growable: false),
    );
  }

  Widget _recordList(
    List<Map<String, dynamic>> records, {
    required String emptyMessage,
    required IconData icon,
  }) {
    if (records.isEmpty) {
      return AppCard(child: Text(emptyMessage, style: AppTextStyles.body));
    }

    return Column(
      children: records
          .take(10)
          .map(
            (record) => Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.sm),
              child: AppCard(
                child: Row(
                  children: [
                    Icon(icon, color: AppColors.primary),
                    const SizedBox(width: AppSpacing.md),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _recordTitle(record),
                            style: AppTextStyles.title,
                          ),
                          const SizedBox(height: 4),
                          Text(
                            _recordDetails(record),
                            style: AppTextStyles.body,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          )
          .toList(growable: false),
    );
  }

  Widget _historyCard(List<PortfolioSyncSnapshot> history) {
    if (history.isEmpty) {
      return AppCard(
        child: Text(
          'No synchronization history yet.',
          style: AppTextStyles.body,
        ),
      );
    }

    return AppCard(
      child: Column(
        children: history
            .take(20)
            .map(
              (snapshot) => Padding(
                padding: const EdgeInsets.symmetric(vertical: AppSpacing.sm),
                child: Row(
                  children: [
                    Icon(
                      snapshot.isSuccessful
                          ? Icons.check_circle_outline
                          : snapshot.isPartial
                          ? Icons.warning_amber_outlined
                          : Icons.error_outline,
                      color: snapshot.isSuccessful
                          ? AppColors.success
                          : snapshot.isPartial
                          ? AppColors.warning
                          : AppColors.danger,
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            '${snapshot.exchangeName} '
                            '${snapshot.status}',
                            style: AppTextStyles.title,
                          ),
                          Text(
                            _formatDate(snapshot.syncedAt),
                            style: AppTextStyles.body,
                          ),
                        ],
                      ),
                    ),
                    Text(
                      _money(snapshot.totalEquityUsd),
                      style: AppTextStyles.title,
                    ),
                  ],
                ),
              ),
            )
            .toList(growable: false),
      ),
    );
  }

  Widget _messageCard(String message, {required bool isError}) {
    final color = isError ? AppColors.danger : AppColors.success;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        children: [
          Icon(
            isError ? Icons.error_outline : Icons.check_circle_outline,
            color: color,
          ),
          const SizedBox(width: AppSpacing.sm),
          Expanded(child: Text(message, style: AppTextStyles.body)),
          IconButton(
            tooltip: 'Dismiss',
            onPressed: () {
              ref.read(livePortfolioProvider.notifier).clearMessages();
            },
            icon: const Icon(Icons.close),
          ),
        ],
      ),
    );
  }

  Widget _warningBox(String message) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: AppColors.warning.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(message, style: AppTextStyles.body),
    );
  }

  Widget _emptyCard({
    required IconData icon,
    required String title,
    required String message,
  }) {
    return AppCard(
      child: Column(
        children: [
          Icon(icon, size: 48, color: AppColors.textSecondary),
          const SizedBox(height: AppSpacing.md),
          Text(title, style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.sm),
          Text(message, textAlign: TextAlign.center, style: AppTextStyles.body),
        ],
      ),
    );
  }

  String _recordTitle(Map<String, dynamic> record) {
    final value = record['symbol'] ?? record['coin'] ?? record['order_id'];

    if (value != null && value.toString().trim().isNotEmpty) {
      return value.toString().trim();
    }

    return 'Exchange record';
  }

  String _recordDetails(Map<String, dynamic> record) {
    final details = <String>[];

    void addDetail(String label, Object? value) {
      if (value == null) {
        return;
      }

      final text = value.toString().trim();

      if (text.isNotEmpty) {
        details.add('$label: $text');
      }
    }

    addDetail('Side', record['side']);
    addDetail('Size', record['size'] ?? record['qty']);
    addDetail(
      'Price',
      record['avg_price'] ?? record['price'] ?? record['order_price'],
    );
    addDetail('Status', record['order_status'] ?? record['position_status']);

    if (details.isEmpty) {
      return 'Exchange data synchronized';
    }

    return details.join(' • ');
  }

  String _money(double value) {
    return '\$${value.toStringAsFixed(2)}';
  }

  String _signedMoney(double value) {
    final sign = value >= 0 ? '+' : '-';

    return '$sign\$${value.abs().toStringAsFixed(2)}';
  }

  String _amount(double value) {
    if (value.abs() >= 1) {
      return value.toStringAsFixed(4);
    }

    return value.toStringAsFixed(8);
  }

  String _formatDate(DateTime value) {
    return value
        .toLocal()
        .toIso8601String()
        .replaceFirst('T', ' ')
        .split('.')
        .first;
  }
}

class _CreateLivePortfolioDialog extends StatefulWidget {
  const _CreateLivePortfolioDialog();

  @override
  State<_CreateLivePortfolioDialog> createState() {
    return _CreateLivePortfolioDialogState();
  }
}

class _CreateLivePortfolioDialogState
    extends State<_CreateLivePortfolioDialog> {
  late final TextEditingController _nameController;
  late final TextEditingController _currencyController;

  String? _validationMessage;

  @override
  void initState() {
    super.initState();

    _nameController = TextEditingController(text: 'Live Portfolio');

    _currencyController = TextEditingController(text: 'USDT');
  }

  @override
  void dispose() {
    _nameController.dispose();
    _currencyController.dispose();

    super.dispose();
  }

  void _submit() {
    final name = _nameController.text.trim();

    final baseCurrency = _currencyController.text.trim().toUpperCase();

    if (name.length < 2) {
      setState(() {
        _validationMessage =
            'Portfolio name must contain at least '
            'two characters.';
      });
      return;
    }

    if (baseCurrency.length < 2) {
      setState(() {
        _validationMessage =
            'Base currency must contain at least '
            'two characters.';
      });
      return;
    }

    Navigator.of(
      context,
    ).pop(<String, String>{'name': name, 'base_currency': baseCurrency});
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Create Live Portfolio'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _nameController,
              maxLength: 150,
              textInputAction: TextInputAction.next,
              decoration: const InputDecoration(
                labelText: 'Portfolio name',
                hintText: 'Live Portfolio',
              ),
            ),
            const SizedBox(height: AppSpacing.sm),
            TextField(
              controller: _currencyController,
              maxLength: 20,
              textCapitalization: TextCapitalization.characters,
              textInputAction: TextInputAction.done,
              onSubmitted: (_) {
                _submit();
              },
              decoration: const InputDecoration(
                labelText: 'Base currency',
                hintText: 'USDT',
              ),
            ),
            if (_validationMessage != null) ...[
              const SizedBox(height: AppSpacing.sm),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  _validationMessage!,
                  style: const TextStyle(color: AppColors.danger),
                ),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () {
            Navigator.of(context).pop();
          },
          child: const Text('Cancel'),
        ),
        FilledButton(onPressed: _submit, child: const Text('Create')),
      ],
    );
  }
}
