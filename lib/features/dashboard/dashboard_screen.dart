import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import '../../core/widgets/coin_logo.dart';
import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../../core/widgets/section_title.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.md),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _topBar(),
              const SizedBox(height: AppSpacing.lg),
              _heroPortfolioCard(),
              const SizedBox(height: AppSpacing.lg),
              _statsGrid(),
              const SizedBox(height: AppSpacing.lg),
              _sectionHeader('Market Overview', 'View All'),
              const SizedBox(height: AppSpacing.sm),
              _marketGrid(context),
              const SizedBox(height: AppSpacing.lg),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(child: _portfolioAllocation()),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(child: _aiInsightCard()),
                ],
              ),
              const SizedBox(height: AppSpacing.lg),
              const SectionTitle('Quick Actions'),
              const SizedBox(height: AppSpacing.sm),
              _quickActions(),
              const SizedBox(height: AppSpacing.xl),
            ],
          ),
        ),
      ),
    );
  }

  Widget _topBar() {
    return Row(
      children: [
        Container(
          height: 42,
          width: 42,
          decoration: BoxDecoration(
            color: AppColors.primary.withValues(alpha: 0.14),
            borderRadius: BorderRadius.circular(14),
          ),
          child: const Icon(Icons.auto_graph, color: AppColors.primary),
        ),
        const SizedBox(width: AppSpacing.sm),
        const Text(
          'P-TRADER ',
          style: TextStyle(
            color: AppColors.textPrimary,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        const Text(
          'AI',
          style: TextStyle(
            color: AppColors.primary,
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        const Spacer(),
        _circleIcon(Icons.search),
        const SizedBox(width: AppSpacing.sm),
        _circleIcon(Icons.notifications_none),
        const SizedBox(width: AppSpacing.sm),
        const CircleAvatar(
          radius: 20,
          backgroundColor: AppColors.primary,
          child: Icon(Icons.person, color: Colors.black),
        ),
      ],
    );
  }

  Widget _circleIcon(IconData icon) {
    return Container(
      height: 42,
      width: 42,
      decoration: BoxDecoration(
        color: AppColors.card,
        shape: BoxShape.circle,
        border: Border.all(color: AppColors.divider),
      ),
      child: Icon(icon, color: AppColors.textPrimary),
    );
  }

  Widget _heroPortfolioCard() {
    return GlassCard(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Total Portfolio Value', style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.sm),
          const Text(
            '\$14,250.00',
            style: TextStyle(
              color: AppColors.textPrimary,
              fontSize: 42,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.md,
                  vertical: AppSpacing.sm,
                ),
                decoration: BoxDecoration(
                  color: AppColors.success.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(50),
                ),
                child: const Row(
                  children: [
                    Icon(
                      Icons.arrow_upward,
                      color: AppColors.success,
                      size: 16,
                    ),
                    SizedBox(width: 4),
                    Text(
                      '\$235.00',
                      style: TextStyle(
                        color: AppColors.success,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              const Text('+1.67% today', style: AppTextStyles.body),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          SizedBox(
            height: 150,
            child: LineChart(
              LineChartData(
                borderData: FlBorderData(show: false),
                titlesData: FlTitlesData(show: false),
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  getDrawingHorizontalLine: (value) {
                    return FlLine(
                      color: AppColors.divider.withValues(alpha: 0.4),
                      strokeWidth: 1,
                    );
                  },
                ),
                lineBarsData: [
                  LineChartBarData(
                    isCurved: true,
                    barWidth: 4,
                    color: AppColors.primary,
                    dotData: FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      color: AppColors.primary.withValues(alpha: 0.16),
                    ),
                    spots: const [
                      FlSpot(0, 2),
                      FlSpot(1, 2.5),
                      FlSpot(2, 2.2),
                      FlSpot(3, 3.1),
                      FlSpot(4, 2.8),
                      FlSpot(5, 3.6),
                      FlSpot(6, 4.2),
                      FlSpot(7, 4),
                      FlSpot(8, 5.1),
                      FlSpot(9, 5.8),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statsGrid() {
    final stats = [
      {
        'title': "Today's P/L",
        'value': '\$235.00',
        'sub': '+1.67%',
        'icon': Icons.account_balance_wallet_outlined,
        'color': AppColors.success,
      },
      {
        'title': 'Active Bots',
        'value': '3',
        'sub': 'Running',
        'icon': Icons.smart_toy_outlined,
        'color': AppColors.primary,
      },
      {
        'title': 'Best Arbitrage',
        'value': '0.91%',
        'sub': 'ETH/USDT',
        'icon': Icons.swap_horiz,
        'color': AppColors.secondary,
      },
      {
        'title': 'Alerts',
        'value': '2',
        'sub': 'New Alerts',
        'icon': Icons.notifications_none,
        'color': AppColors.warning,
      },
    ];

    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth > 800;

        return GridView.count(
          crossAxisCount: isWide ? 4 : 2,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: AppSpacing.md,
          mainAxisSpacing: AppSpacing.md,
          childAspectRatio: isWide ? 2.3 : 1.15,
          children: stats.map((stat) {
            final color = stat['color'] as Color;
            return GlassCard(
              padding: const EdgeInsets.all(10),
              child: Row(
                children: [
                  CircleAvatar(
                    radius: 16,
                    backgroundColor: color.withValues(alpha: 0.15),
                    child: Icon(
                      stat['icon'] as IconData,
                      color: color,
                      size: 16,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          stat['title'].toString(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTextStyles.body.copyWith(fontSize: 11),
                        ),
                        Text(
                          stat['value'].toString(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: AppTextStyles.title.copyWith(fontSize: 16),
                        ),
                        Text(
                          stat['sub'].toString(),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: color,
                            fontWeight: FontWeight.w600,
                            fontSize: 11,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }).toList(),
        );
      },
    );
  }

  Widget _sectionHeader(String title, String action) {
    return Row(
      children: [
        Text(title, style: AppTextStyles.title),
        const Spacer(),
        Text(
          action,
          style: const TextStyle(
            color: AppColors.primary,
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }

  Widget _marketGrid(BuildContext context) {
    final markets = [
      {
        'pair': 'BTC/USDT',
        'price': '67,891.45',
        'change': '+1.67%',
        'icon': '₿',
        'color': Colors.orange,
      },
      {
        'pair': 'ETH/USDT',
        'price': '3,467.21',
        'change': '+2.45%',
        'icon': 'Ξ',
        'color': Colors.blueAccent,
      },
      {
        'pair': 'SOL/USDT',
        'price': '152.35',
        'change': '+3.12%',
        'icon': 'S',
        'color': Colors.purpleAccent,
      },
      {
        'pair': 'BNB/USDT',
        'price': '591.80',
        'change': '+1.41%',
        'icon': 'B',
        'color': Colors.amber,
      },
    ];

    return GridView.count(
      crossAxisCount: MediaQuery.of(context).size.width > 800 ? 4 : 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: AppSpacing.md,
      mainAxisSpacing: AppSpacing.md,
      childAspectRatio: 2,
      children: markets.map((market) {
        return GlassCard(
          child: Row(
            children: [
              CoinLogo(
                symbol: market['pair']
                    .toString()
                    .split('/')
                    .first
                    .toLowerCase(),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(market['pair'].toString(), style: AppTextStyles.title),
                    const Spacer(),
                    Text(
                      market['price'].toString(),
                      style: const TextStyle(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      market['change'].toString(),
                      style: const TextStyle(
                        color: AppColors.success,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.show_chart, color: AppColors.success),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _portfolioAllocation() {
    final allocations = [
      ['BTC', '45%', AppColors.primary],
      ['ETH', '25%', Colors.deepPurpleAccent],
      ['SOL', '15%', AppColors.success],
      ['XRP', '10%', AppColors.warning],
      ['Cash', '5%', AppColors.textSecondary],
    ];

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Portfolio Allocation', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.md),
          SizedBox(
            height: 160,
            child: PieChart(
              PieChartData(
                centerSpaceRadius: 42,
                sectionsSpace: 2,
                sections: [
                  PieChartSectionData(
                    value: 45,
                    color: AppColors.primary,
                    title: '',
                    radius: 48,
                  ),
                  PieChartSectionData(
                    value: 25,
                    color: Colors.deepPurpleAccent,
                    title: '',
                    radius: 48,
                  ),
                  PieChartSectionData(
                    value: 15,
                    color: AppColors.success,
                    title: '',
                    radius: 48,
                  ),
                  PieChartSectionData(
                    value: 10,
                    color: AppColors.warning,
                    title: '',
                    radius: 48,
                  ),
                  PieChartSectionData(
                    value: 5,
                    color: AppColors.textSecondary,
                    title: '',
                    radius: 48,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.md),
          Column(
            children: allocations.map((item) {
              return Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.sm),
                child: Row(
                  children: [
                    Container(
                      height: 9,
                      width: 9,
                      decoration: BoxDecoration(
                        color: item[2] as Color,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: AppSpacing.sm),
                    Expanded(
                      child: Text(
                        item[0].toString(),
                        style: AppTextStyles.body,
                      ),
                    ),
                    Text(
                      item[1].toString(),
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

  Widget _aiInsightCard() {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.auto_awesome, color: Colors.deepPurpleAccent),
              const SizedBox(width: AppSpacing.sm),
              const Expanded(
                child: Text('AI Market Insight', style: AppTextStyles.title),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.sm,
                  vertical: AppSpacing.xs,
                ),
                decoration: BoxDecoration(
                  color: Colors.deepPurpleAccent.withValues(alpha: 0.16),
                  borderRadius: BorderRadius.circular(30),
                ),
                child: const Text(
                  'AI',
                  style: TextStyle(
                    color: Colors.deepPurpleAccent,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          const Text(
            'Bitcoin is showing strong momentum above \$67K with increased volume. Watch for potential breakout above \$68.5K resistance.',
            style: AppTextStyles.body,
          ),
          const SizedBox(height: AppSpacing.lg),
          const Row(
            children: [
              Text('Confidence', style: AppTextStyles.body),
              Spacer(),
              Text(
                'High',
                style: TextStyle(
                  color: AppColors.success,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.sm),
          ClipRRect(
            borderRadius: BorderRadius.circular(50),
            child: LinearProgressIndicator(
              value: 0.88,
              minHeight: 8,
              color: Colors.deepPurpleAccent,
              backgroundColor: AppColors.divider,
            ),
          ),
          const SizedBox(height: AppSpacing.lg),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(AppSpacing.radius),
              border: Border.all(
                color: Colors.deepPurpleAccent.withValues(alpha: 0.35),
              ),
            ),
            child: const Center(
              child: Text(
                'Ask AI Assistant',
                style: TextStyle(
                  color: Colors.deepPurpleAccent,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _quickActions() {
    final actions = [
      ['Buy', 'Crypto', Icons.shopping_cart_outlined, AppColors.success],
      ['Deposit', 'Funds', Icons.file_download_outlined, Colors.blueAccent],
      [
        'Create Bot',
        'New Bot',
        Icons.smart_toy_outlined,
        Colors.deepPurpleAccent,
      ],
      ['Arbitrage', 'Scanner', Icons.swap_horiz, AppColors.secondary],
      ['AI Assistant', 'Chat Now', Icons.auto_awesome, Colors.deepPurpleAccent],
    ];

    return SizedBox(
      height: 110,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: actions.length,
        separatorBuilder: (context, index) =>
            const SizedBox(width: AppSpacing.md),
        itemBuilder: (context, index) {
          final item = actions[index];
          final color = item[3] as Color;

          return SizedBox(
            width: 160,
            child: GlassCard(
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: color.withValues(alpha: 0.16),
                    child: Icon(item[2] as IconData, color: color),
                  ),
                  const SizedBox(width: AppSpacing.sm),
                  Expanded(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          item[0].toString(),
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        Text(item[1].toString(), style: AppTextStyles.body),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
