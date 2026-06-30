import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/app_card.dart';
import '../../core/widgets/section_title.dart';
import '../../core/widgets/coin_logo.dart';

class PortfolioScreen extends StatelessWidget {
  const PortfolioScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Portfolio'),
        actions: [
          IconButton(
            onPressed: () {},
            icon: const Icon(Icons.add_circle_outline),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _balanceCard(),
            const SizedBox(height: AppSpacing.lg),

            const SectionTitle('Portfolio Allocation'),
            const SizedBox(height: AppSpacing.sm),
            _allocationCard(),

            const SizedBox(height: AppSpacing.lg),
            const SectionTitle('Assets'),
            const SizedBox(height: AppSpacing.sm),
            _assetList(),

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

  Widget _balanceCard() {
    return AppCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Total Balance', style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.sm),
          const Text('\$14,250.00', style: AppTextStyles.heading),
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
                child: const Text(
                  '+\$235.00',
                  style: TextStyle(
                    color: AppColors.success,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              const Text('+1.67% today', style: AppTextStyles.body),
            ],
          ),
        ],
      ),
    );
  }

  Widget _allocationCard() {
    final items = [
      _AllocationItem('BTC', '45%', AppColors.primary),
      _AllocationItem('ETH', '25%', AppColors.secondary),
      _AllocationItem('SOL', '15%', AppColors.success),
      _AllocationItem('XRP', '10%', AppColors.warning),
      _AllocationItem('Cash', '5%', AppColors.textSecondary),
    ];

    return AppCard(
      child: Column(
        children: [
          SizedBox(
            height: 210,
            child: PieChart(
              PieChartData(
                centerSpaceRadius: 58,
                sectionsSpace: 3,
                sections: [
                  PieChartSectionData(
                    value: 45,
                    color: AppColors.primary,
                    title: 'BTC',
                    radius: 54,
                    titleStyle: const TextStyle(
                      color: Colors.black,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  PieChartSectionData(
                    value: 25,
                    color: AppColors.secondary,
                    title: 'ETH',
                    radius: 50,
                    titleStyle: const TextStyle(
                      color: Colors.black,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  PieChartSectionData(
                    value: 15,
                    color: AppColors.success,
                    title: 'SOL',
                    radius: 46,
                    titleStyle: const TextStyle(
                      color: Colors.black,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  PieChartSectionData(
                    value: 10,
                    color: AppColors.warning,
                    title: 'XRP',
                    radius: 42,
                    titleStyle: const TextStyle(
                      color: Colors.black,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  PieChartSectionData(
                    value: 5,
                    color: AppColors.textSecondary,
                    title: '',
                    radius: 38,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Column(
            children: items.map((item) {
              return Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: Row(
                  children: [
                    Container(
                      height: 10,
                      width: 10,
                      decoration: BoxDecoration(
                        color: item.color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(child: Text(item.name, style: AppTextStyles.body)),
                    Text(
                      item.percent,
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

  Widget _assetList() {
    final assets = [
      {
        'symbol': 'BTC',
        'name': 'Bitcoin',
        'amount': '0.245 BTC',
        'value': '\$10,830',
        'profit': '+\$1,245',
        'positive': true,
      },
      {
        'symbol': 'ETH',
        'name': 'Ethereum',
        'amount': '3.52 ETH',
        'value': '\$2,630',
        'profit': '+\$420',
        'positive': true,
      },
      {
        'symbol': 'SOL',
        'name': 'Solana',
        'amount': '25.1 SOL',
        'value': '\$154',
        'profit': '-\$36',
        'positive': false,
      },
      {
        'symbol': 'XRP',
        'name': 'Ripple',
        'amount': '530 XRP',
        'value': '\$0.51',
        'profit': '+\$18',
        'positive': true,
      },
    ];

    return Column(
      children: assets.map((asset) {
        final positive = asset['positive'] as bool;

        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: AppCard(
            child: Row(
              children: [
                CoinLogo(symbol: asset['symbol'].toString().toLowerCase()),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        asset['symbol'].toString(),
                        style: AppTextStyles.title,
                      ),
                      Text(
                        asset['amount'].toString(),
                        style: AppTextStyles.body,
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(asset['value'].toString(), style: AppTextStyles.title),
                    Text(
                      asset['profit'].toString(),
                      style: TextStyle(
                        color: positive ? AppColors.success : AppColors.danger,
                        fontWeight: FontWeight.bold,
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

class _AllocationItem {
  final String name;
  final String percent;
  final Color color;

  const _AllocationItem(this.name, this.percent, this.color);
}
