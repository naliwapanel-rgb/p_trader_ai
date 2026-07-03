import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/app_card.dart';
import '../../core/widgets/section_title.dart';
import '../../core/widgets/coin_logo.dart';
import 'providers/portfolio_provider.dart';
import 'data/portfolio_holding.dart';
import '../../providers/market_providers.dart';

class PortfolioScreen extends ConsumerWidget {
  const PortfolioScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final marketsAsync = ref.watch(liveMarketsProvider);
    final holdings = ref.watch(portfolioHoldingsProvider);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Portfolio'),
        actions: [
          IconButton(
            onPressed: () {
              _showAddHoldingDialog(context, ref);
            },
            icon: const Icon(Icons.add_circle_outline),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            marketsAsync.when(
              loading: () => _balanceCard(
                totalValue: 0,
                totalProfit: 0,
                profitPercentage: 0,
              ),
              error: (error, stackTrace) => _balanceCard(
                totalValue: 0,
                totalProfit: 0,
                profitPercentage: 0,
              ),
              data: (coins) {
                double totalValue = 0;
                double totalCost = 0;

                for (final holding in holdings) {
                  final coin = coins.cast<dynamic>().firstWhere(
                    (c) => c.id == holding.coinId,
                    orElse: () => null,
                  );

                  final price = coin?.currentPrice ?? holding.averageBuyPrice;

                  totalValue += holding.amount * price;
                  totalCost += holding.amount * holding.averageBuyPrice;
                }

                final totalProfit = totalValue - totalCost;

                final profitPercentage = totalCost == 0
                    ? 0.0
                    : (totalProfit / totalCost) * 100;

                return _balanceCard(
                  totalValue: totalValue,
                  totalProfit: totalProfit,
                  profitPercentage: profitPercentage,
                );
              },
            ),
            const SizedBox(height: AppSpacing.lg),

            const SectionTitle('Portfolio Allocation'),
            const SizedBox(height: AppSpacing.sm),
            marketsAsync.when(
              loading: () => _allocationCard(holdings, const []),
              error: (error, stackTrace) => _allocationCard(holdings, const []),
              data: (coins) => _allocationCard(holdings, coins),
            ),

            const SizedBox(height: AppSpacing.lg),
            const SectionTitle('Assets'),
            const SizedBox(height: AppSpacing.sm),
            marketsAsync.when(
              loading: () => _assetList(holdings, const []),
              error: (error, stackTrace) => _assetList(holdings, const []),
              data: (coins) => _assetList(holdings, coins),
            ),

            const SizedBox(height: AppSpacing.lg),
            const SectionTitle('Recent Transactions'),
            const SizedBox(height: AppSpacing.sm),
            _transactionList(),

            const SizedBox(height: AppSpacing.xl),
          ],
        ),
      ),
    );
  }

  void _showAddHoldingDialog(BuildContext context, WidgetRef ref) {
    final coinIdController = TextEditingController();
    final symbolController = TextEditingController();
    final amountController = TextEditingController();
    final averageBuyPriceController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          title: const Text('Add Holding'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: coinIdController,
                decoration: const InputDecoration(
                  labelText: 'Coin ID',
                  hintText: 'bitcoin',
                ),
              ),
              TextField(
                controller: symbolController,
                decoration: const InputDecoration(
                  labelText: 'Symbol',
                  hintText: 'BTC',
                ),
              ),
              TextField(
                controller: amountController,
                decoration: const InputDecoration(
                  labelText: 'Amount',
                  hintText: '0.25',
                ),
                keyboardType: TextInputType.number,
              ),
              TextField(
                controller: averageBuyPriceController,
                decoration: const InputDecoration(
                  labelText: 'Average Buy Price',
                  hintText: '65000',
                ),
                keyboardType: TextInputType.number,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
              },
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                final coinId = coinIdController.text.trim().toLowerCase();
                final symbol = symbolController.text.trim().toUpperCase();
                final amount = double.tryParse(amountController.text.trim());
                final averageBuyPrice = double.tryParse(
                  averageBuyPriceController.text.trim(),
                );

                if (coinId.isEmpty ||
                    symbol.isEmpty ||
                    amount == null ||
                    averageBuyPrice == null ||
                    amount <= 0 ||
                    averageBuyPrice <= 0) {
                  return;
                }

                final holding = PortfolioHolding(
                  coinId: coinId,
                  symbol: symbol,
                  name: symbol,
                  amount: amount,
                  averageBuyPrice: averageBuyPrice,
                );

                await ref
                    .read(portfolioHoldingsProvider.notifier)
                    .addHolding(holding);

                if (context.mounted) {
                  Navigator.pop(context);
                }
              },
              child: const Text('Save'),
            ),
          ],
        );
      },
    );
  }

  Widget _balanceCard({
    required double totalValue,
    required double totalProfit,
    required double profitPercentage,
  }) {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Total Balance', style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.sm),
          Text(
            '\$${totalValue.toStringAsFixed(2)}',
            style: AppTextStyles.heading,
          ),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(50),
                ),
                child: Text(
                  '+\$${totalProfit.toStringAsFixed(2)}',
                  style: TextStyle(
                    color: AppColors.success,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Text(
                '${profitPercentage >= 0 ? "+" : ""}${profitPercentage.toStringAsFixed(2)}%',
                style: AppTextStyles.body,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _allocationCard(List<PortfolioHolding> holdings, List coins) {
    if (holdings.isEmpty) {
      return AppCard(
        child: Text(
          'Add holdings to see your portfolio allocation.',
          style: AppTextStyles.body,
        ),
      );
    }

    final colors = [
      AppColors.primary,
      AppColors.secondary,
      AppColors.success,
      AppColors.warning,
      AppColors.textSecondary,
    ];

    final allocationItems = holdings.map((holding) {
      final coin = coins.cast<dynamic>().firstWhere(
        (item) => item.id == holding.coinId,
        orElse: () => null,
      );

      final price = coin?.currentPrice ?? holding.averageBuyPrice;
      final value = holding.amount * price;

      return {'symbol': holding.symbol, 'value': value};
    }).toList();

    final totalValue = allocationItems.fold<double>(
      0,
      (sum, item) => sum + (item['value'] as double),
    );

    final portfolioAllocation = allocationItems.map((item) {
      final value = item['value'] as double;

      return {
        'symbol': item['symbol'] as String,
        'percentage': totalValue == 0 ? 0.0 : (value / totalValue) * 100,
      };
    }).toList();

    return AppCard(
      child: Column(
        children: [
          SizedBox(
            height: 210,
            child: PieChart(
              PieChartData(
                centerSpaceRadius: 58,
                sectionsSpace: 3,
                sections: portfolioAllocation.asMap().entries.map((entry) {
                  final index = entry.key;
                  final item = entry.value;
                  final percentage = item['percentage'] as double;

                  return PieChartSectionData(
                    value: percentage,
                    color: colors[index % colors.length],
                    title: item['symbol'].toString(),
                    radius: 54,
                    titleStyle: const TextStyle(
                      color: Colors.black,
                      fontWeight: FontWeight.bold,
                    ),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Column(
            children: portfolioAllocation.asMap().entries.map((entry) {
              final index = entry.key;
              final item = entry.value;
              final percentage = item['percentage'] as double;

              return Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: Row(
                  children: [
                    Container(
                      height: 10,
                      width: 10,
                      decoration: BoxDecoration(
                        color: colors[index % colors.length],
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(
                        item['symbol'].toString(),
                        style: AppTextStyles.body,
                      ),
                    ),
                    Text(
                      '${percentage.toStringAsFixed(1)}%',
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              );
            }).toList(),
          ),
        ],
      ),
    );
  }

  Widget _assetList(List<PortfolioHolding> holdings, List coins) {
    coins;
    if (holdings.isEmpty) {
      return AppCard(
        child: Column(
          children: [
            const Icon(Icons.account_balance_wallet_outlined, size: 48),
            const SizedBox(height: AppSpacing.md),
            Text('No holdings yet', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Tap the plus button to add your first portfolio asset.',
              textAlign: TextAlign.center,
              style: AppTextStyles.body,
            ),
          ],
        ),
      );
    }

    return Column(
      children: holdings.map((holding) {
        final coin = coins.cast<dynamic>().firstWhere(
          (item) => item.id == holding.coinId,
          orElse: () => null,
        );

        final currentPrice = coin?.currentPrice ?? holding.averageBuyPrice;

        final currentValue = holding.amount * currentPrice;
        final costBasis = holding.amount * holding.averageBuyPrice;
        final profitLoss = currentValue - costBasis;
        final profitLossPercentage = costBasis == 0
            ? 0
            : (profitLoss / costBasis) * 100;

        final isProfit = profitLoss >= 0;
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: AppCard(
            child: Row(
              children: [
                CoinLogo(symbol: holding.symbol.toLowerCase()),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(holding.symbol, style: AppTextStyles.title),
                      Text(
                        '${holding.amount} ${holding.symbol}',
                        style: AppTextStyles.body,
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'Value \$${currentValue.toStringAsFixed(2)}',
                      style: AppTextStyles.title,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${isProfit ? "+" : ""}\$${profitLoss.toStringAsFixed(2)} '
                      '(${profitLossPercentage.toStringAsFixed(2)}%)',
                      style: TextStyle(
                        color: isProfit ? AppColors.success : AppColors.danger,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      'Avg \$${holding.averageBuyPrice.toStringAsFixed(2)}',
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _transactionList() {
    final transactions = [
      {
        'type': 'Buy BTC',
        'date': 'Today, 09:30',
        'amount': '+0.012 BTC',
        'icon': Icons.call_received,
        'color': AppColors.success,
      },
      {
        'type': 'Sell ETH',
        'date': 'Today, 08:45',
        'amount': '-0.25 ETH',
        'icon': Icons.call_made,
        'color': AppColors.danger,
      },
      {
        'type': 'Deposit',
        'date': 'Yesterday',
        'amount': '+\$500',
        'icon': Icons.account_balance_wallet,
        'color': AppColors.primary,
      },
      {
        'type': 'Withdraw',
        'date': '2 days ago',
        'amount': '-\$120',
        'icon': Icons.outbound,
        'color': AppColors.warning,
      },
    ];

    return Column(
      children: transactions.map((tx) {
        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: AppCard(
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: (tx['color'] as Color).withValues(
                    alpha: 0.15,
                  ),
                  child: Icon(
                    tx['icon'] as IconData,
                    color: tx['color'] as Color,
                  ),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(tx['type'].toString(), style: AppTextStyles.title),
                      Text(tx['date'].toString(), style: AppTextStyles.body),
                    ],
                  ),
                ),
                Text(
                  tx['amount'].toString(),
                  style: const TextStyle(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}
