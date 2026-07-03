import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../../domain/entities/crypto_asset.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../watchlist/providers/watchlist_provider.dart';

class MarketDetailsScreen extends ConsumerWidget {
  final CryptoAsset coin;

  const MarketDetailsScreen({super.key, required this.coin});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isPositive = coin.priceChangePercentage24h >= 0;
    final changePrefix = isPositive ? '+' : '';

    final watchlist = ref.watch(watchlistCoinIdsProvider);
    final isFavorite = watchlist.contains(coin.id);

    return Scaffold(
      appBar: AppBar(
        title: Text('${coin.symbol.toUpperCase()} Market'),
        actions: [
          IconButton(
            onPressed: () {
              ref.read(watchlistCoinIdsProvider.notifier).toggleCoin(coin.id);
            },
            icon: Icon(
              isFavorite ? Icons.star : Icons.star_border,
              color: isFavorite ? Colors.amber : Colors.white,
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _heroCard(isPositive, changePrefix),
            const SizedBox(height: AppSpacing.lg),
            _actionButtons(),
            const SizedBox(height: AppSpacing.lg),
            _chartPlaceholder(),
            const SizedBox(height: AppSpacing.lg),
            _statsGrid(),
            const SizedBox(height: AppSpacing.lg),
            _performanceSection(),
            const SizedBox(height: AppSpacing.lg),
            _marketDepthSection(),
            const SizedBox(height: AppSpacing.lg),
            _athAtlSection(),
            const SizedBox(height: AppSpacing.lg),
            _lastUpdatedSection(),
            const SizedBox(height: AppSpacing.lg),
            _availableExchanges(),
            const SizedBox(height: AppSpacing.lg),
            _tradingStatusSection(),
            const SizedBox(height: AppSpacing.lg),
            _aiInsight(isPositive),
          ],
        ),
      ),
    );
  }

  Widget _performanceSection() {
    final isPositive = coin.priceChangePercentage24h >= 0;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Performance', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: _detailMetric(
                  '24H Change',
                  '${isPositive ? '+' : ''}${coin.priceChangePercentage24h.toStringAsFixed(2)}%',
                  isPositive ? AppColors.success : AppColors.danger,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _detailMetric(
                  'Rank',
                  '#${coin.marketCapRank}',
                  AppColors.primary,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _tradingStatusSection() {
    final isPositive = coin.priceChangePercentage24h >= 0;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Trading Status', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.md),
          Row(
            children: [
              Expanded(
                child: _detailMetric(
                  'Momentum',
                  isPositive ? 'Bullish' : 'Bearish',
                  isPositive ? AppColors.success : AppColors.danger,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _detailMetric(
                  'Liquidity',
                  coin.totalVolume > 1000000000 ? 'High' : 'Moderate',
                  AppColors.primary,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          _infoRow('Tracking Pair', '${coin.symbol.toUpperCase()}/USDT'),
          _infoRow('Refresh Mode', 'Auto + Pull Refresh'),
          _infoRow('Risk Note', 'Market data only. Not financial advice.'),
        ],
      ),
    );
  }

  Widget _lastUpdatedSection() {
    return GlassCard(
      child: Row(
        children: [
          const Icon(Icons.access_time, color: AppColors.primary),
          const SizedBox(width: AppSpacing.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Live Market Data', style: AppTextStyles.title),
                const SizedBox(height: AppSpacing.xs),
                Text(
                  'Updated ${_formatDateTime(coin.lastUpdated)} • Source: CoinGecko',
                  style: AppTextStyles.body,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  String _formatDateTime(DateTime date) {
    final hour = date.hour.toString().padLeft(2, '0');
    final minute = date.minute.toString().padLeft(2, '0');

    return '${date.day}/${date.month}/${date.year} $hour:$minute';
  }

  Widget _athAtlSection() {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Price History', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.md),
          _infoRow(
            'All-Time High',
            '\$${coin.ath.toStringAsFixed(coin.ath < 1 ? 4 : 2)}',
          ),
          _infoRow(
            'From ATH',
            '${coin.athChangePercentage.toStringAsFixed(2)}%',
          ),
          _infoRow('ATH Date', _formatDate(coin.athDate)),
          const Divider(color: AppColors.divider),
          _infoRow(
            'All-Time Low',
            '\$${coin.atl.toStringAsFixed(coin.atl < 1 ? 4 : 2)}',
          ),
          _infoRow(
            'From ATL',
            '+${coin.atlChangePercentage.toStringAsFixed(2)}%',
          ),
          _infoRow('ATL Date', _formatDate(coin.atlDate)),
        ],
      ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year}';
  }

  Widget _marketDepthSection() {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Market Statistics', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.md),
          _infoRow('Market Cap', _formatLargeNumber(coin.marketCap)),
          _infoRow('24H Volume', _formatLargeNumber(coin.totalVolume)),
          _infoRow(
            'Current Price',
            '\$${coin.currentPrice.toStringAsFixed(coin.currentPrice < 1 ? 4 : 2)}',
          ),
          _infoRow('Pair', '${coin.symbol.toUpperCase()}/USDT'),
          _infoRow('Data Source', 'CoinGecko'),
        ],
      ),
    );
  }

  Widget _availableExchanges() {
    final exchanges = ['Binance', 'Bybit', 'OKX', 'Kraken', 'Coinbase'];

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Available Exchanges', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.md),

          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: exchanges
                .map(
                  (exchange) => Chip(
                    avatar: const Icon(
                      Icons.check_circle,
                      color: AppColors.success,
                      size: 18,
                    ),
                    label: Text(exchange),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }

  Widget _detailMetric(String label, String value, Color color) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(AppSpacing.radius),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.xs),
          Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: Row(
        children: [
          Expanded(child: Text(label, style: AppTextStyles.body)),
          Text(
            value,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _heroCard(bool isPositive, String changePrefix) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 30,
                backgroundColor: AppColors.card,
                backgroundImage: NetworkImage(coin.image),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(coin.name, style: AppTextStyles.heading),
                    Text(
                      '${coin.symbol.toUpperCase()}/USDT',
                      style: AppTextStyles.body,
                    ),
                  ],
                ),
              ),
              _badge('Rank #${coin.marketCapRank}', AppColors.primary),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(
            '\$${coin.currentPrice.toStringAsFixed(coin.currentPrice < 1 ? 4 : 2)}',
            style: AppTextStyles.heading.copyWith(fontSize: 34),
          ),
          const SizedBox(height: AppSpacing.sm),
          _badge(
            '$changePrefix${coin.priceChangePercentage24h.toStringAsFixed(2)}% 24h',
            isPositive ? AppColors.success : AppColors.danger,
          ),
        ],
      ),
    );
  }

  Widget _badge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.md,
        vertical: AppSpacing.sm,
      ),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(50),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.bold,
          fontSize: 12,
        ),
      ),
    );
  }

  Widget _actionButtons() {
    return Row(
      children: [
        Expanded(
          child: _actionButton('Buy', Icons.trending_up, AppColors.success),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: _actionButton('Sell', Icons.trending_down, AppColors.danger),
        ),
      ],
    );
  }

  Widget _actionButton(String text, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(AppSpacing.radius),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: color),
          const SizedBox(width: AppSpacing.sm),
          Text(
            text,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _chartPlaceholder() {
    final chartData = _generateChartData();
    final isPositive = coin.priceChangePercentage24h >= 0;
    final chartColor = isPositive ? AppColors.success : AppColors.danger;

    final minY =
        chartData.map((e) => e.y).reduce((a, b) => a < b ? a : b) * 0.995;
    final maxY =
        chartData.map((e) => e.y).reduce((a, b) => a > b ? a : b) * 1.005;

    return GlassCard(
      child: SizedBox(
        height: 280,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Text('Price Chart', style: AppTextStyles.title),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppSpacing.sm,
                    vertical: AppSpacing.xs,
                  ),
                  decoration: BoxDecoration(
                    color: chartColor.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(50),
                    border: Border.all(
                      color: chartColor.withValues(alpha: 0.35),
                    ),
                  ),
                  child: Text(
                    isPositive ? 'Bullish' : 'Bearish',
                    style: TextStyle(
                      color: chartColor,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Expanded(
              child: LineChart(
                LineChartData(
                  minY: minY,
                  maxY: maxY,
                  lineTouchData: LineTouchData(
                    enabled: true,
                    touchTooltipData: LineTouchTooltipData(
                      tooltipRoundedRadius: 12,
                      getTooltipItems: (spots) {
                        return spots.map((spot) {
                          return LineTooltipItem(
                            '\$${spot.y.toStringAsFixed(coin.currentPrice < 1 ? 4 : 2)}',
                            TextStyle(
                              color: chartColor,
                              fontWeight: FontWeight.bold,
                            ),
                          );
                        }).toList();
                      },
                    ),
                  ),
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: coin.currentPrice * 0.01,
                    getDrawingHorizontalLine: (_) => FlLine(
                      color: AppColors.divider.withValues(alpha: 0.22),
                      strokeWidth: 1,
                    ),
                  ),
                  titlesData: const FlTitlesData(
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    topTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                  ),
                  borderData: FlBorderData(show: false),
                  lineBarsData: [
                    LineChartBarData(
                      spots: chartData,
                      isCurved: true,
                      barWidth: 4,
                      isStrokeCapRound: true,
                      dotData: FlDotData(
                        show: true,
                        checkToShowDot: (spot, barData) {
                          return spot.x == chartData.last.x;
                        },
                      ),
                      belowBarData: BarAreaData(
                        show: true,
                        color: chartColor.withValues(alpha: 0.13),
                      ),
                      color: chartColor,
                    ),
                  ],
                ),
                duration: const Duration(milliseconds: 900),
                curve: Curves.easeOutCubic,
              ),
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: const [
                _TimeChip('1H'),
                _TimeChip('4H'),
                _TimeChip('1D'),
                _TimeChip('1W'),
                _TimeChip('1M'),
                _TimeChip('1Y'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _statsGrid() {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _statCard(
                'Market Cap',
                _formatLargeNumber(coin.marketCap),
              ),
            ),
            const SizedBox(width: AppSpacing.md),
            Expanded(
              child: _statCard(
                '24h Volume',
                _formatLargeNumber(coin.totalVolume),
              ),
            ),
          ],
        ),
        const SizedBox(height: AppSpacing.md),
        Row(
          children: [
            Expanded(child: _statCard('Rank', '#${coin.marketCapRank}')),
            const SizedBox(width: AppSpacing.md),
            Expanded(child: _statCard('Symbol', coin.symbol.toUpperCase())),
          ],
        ),
      ],
    );
  }

  Widget _statCard(String title, String value) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.xs),
          Text(value, style: AppTextStyles.title),
        ],
      ),
    );
  }

  Widget _aiInsight(bool isPositive) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('AI Market Insight', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.sm),
          Text(
            isPositive
                ? 'Momentum is positive. Buyers are currently controlling short-term price action. Watch for pullback entries near support.'
                : 'Momentum is weak. Sellers are currently pressuring the market. Wait for confirmation before entering long positions.',
            style: AppTextStyles.body,
          ),
        ],
      ),
    );
  }

  List<FlSpot> _generateChartData() {
    final basePrice = coin.currentPrice;
    final isPositive = coin.priceChangePercentage24h >= 0;

    final multipliers = isPositive
        ? [0.985, 0.992, 0.988, 1.002, 0.997, 1.008, 1.015, 1.011, 1.024]
        : [1.018, 1.012, 1.006, 0.998, 1.002, 0.991, 0.986, 0.981, 0.974];

    return List.generate(
      multipliers.length,
      (index) => FlSpot(index.toDouble(), basePrice * multipliers[index]),
    );
  }

  String _formatLargeNumber(double value) {
    if (value >= 1000000000000) {
      return '\$${(value / 1000000000000).toStringAsFixed(2)}T';
    }
    if (value >= 1000000000) {
      return '\$${(value / 1000000000).toStringAsFixed(2)}B';
    }
    if (value >= 1000000) {
      return '\$${(value / 1000000).toStringAsFixed(2)}M';
    }
    return '\$${value.toStringAsFixed(2)}';
  }
}

class _TimeChip extends StatelessWidget {
  final String text;

  const _TimeChip(this.text);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.sm,
        vertical: AppSpacing.xs,
      ),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(50),
        border: Border.all(color: AppColors.divider),
      ),
      child: Text(text, style: AppTextStyles.body),
    );
  }
}
