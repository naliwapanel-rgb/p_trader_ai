import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../../core/widgets/coin_logo.dart';

class ArbitrageScreen extends StatelessWidget {
  const ArbitrageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final opportunities = [
      {
        'pair': 'ETH/USDT',
        'buy': 'Bybit',
        'sell': 'Binance',
        'buyPrice': '\$3,461.20',
        'sellPrice': '\$3,492.70',
        'spread': '0.91%',
        'profit': '+\$23.90',
        'confidence': '92%',
        'color': AppColors.primary,
      },
      {
        'pair': 'BTC/USDT',
        'buy': 'Binance',
        'sell': 'OKX',
        'buyPrice': '\$67,810.00',
        'sellPrice': '\$68,366.00',
        'spread': '0.82%',
        'profit': '+\$18.20',
        'confidence': '88%',
        'color': AppColors.success,
      },
      {
        'pair': 'SOL/USDT',
        'buy': 'KuCoin',
        'sell': 'Bybit',
        'buyPrice': '\$151.82',
        'sellPrice': '\$152.79',
        'spread': '0.64%',
        'profit': '+\$9.70',
        'confidence': '81%',
        'color': AppColors.warning,
      },
      {
        'pair': 'XRP/USDT',
        'buy': 'OKX',
        'sell': 'Binance',
        'buyPrice': '\$0.512',
        'sellPrice': '\$0.515',
        'spread': '0.58%',
        'profit': '+\$4.10',
        'confidence': '76%',
        'color': AppColors.secondary,
      },
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Arbitrage'),
        actions: [
          IconButton(onPressed: () {}, icon: const Icon(Icons.refresh)),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _scannerStatus(),
            const SizedBox(height: AppSpacing.lg),
            const Text('Best Opportunities', style: AppTextStyles.title),
            const SizedBox(height: AppSpacing.sm),
            ...opportunities.map((item) => _opportunityCard(item)),
            const SizedBox(height: AppSpacing.xl),
          ],
        ),
      ),
    );
  }

  Widget _scannerStatus() {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                backgroundColor: AppColors.success.withValues(alpha: 0.15),
                child: const Icon(Icons.radar, color: AppColors.success),
              ),
              const SizedBox(width: AppSpacing.md),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Scanner Online', style: AppTextStyles.title),
                    Text('Monitoring 6 exchanges', style: AppTextStyles.body),
                  ],
                ),
              ),
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
                  'LIVE',
                  style: TextStyle(
                    color: AppColors.success,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          Row(
            children: [
              Expanded(
                child: _statusInfo(
                  label: 'Opportunities',
                  value: '12',
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: _statusInfo(
                  label: 'Best Spread',
                  value: '0.91%',
                  color: AppColors.success,
                ),
              ),
              const SizedBox(width: AppSpacing.sm),
              Expanded(
                child: _statusInfo(
                  label: 'Est. Daily',
                  value: '+\$85',
                  color: AppColors.warning,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _statusInfo({
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.body.copyWith(fontSize: 12)),
          const SizedBox(height: AppSpacing.xs),
          Text(
            value,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 18,
            ),
          ),
        ],
      ),
    );
  }

  Widget _opportunityCard(Map<String, Object> item) {
    final color = item['color'] as Color;

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.md),
      child: GlassCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                CoinLogo(
                  symbol: item['pair']
                      .toString()
                      .split('/')
                      .first
                      .toLowerCase(),
                ),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(item['pair'].toString(), style: AppTextStyles.title),
                      Text(
                        '${item['buy']} → ${item['sell']}',
                        style: AppTextStyles.body,
                      ),
                    ],
                  ),
                ),
                Text(
                  item['spread'].toString(),
                  style: TextStyle(
                    color: color,
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                Expanded(
                  child: _priceBox(
                    label: 'Buy Price',
                    value: item['buyPrice'].toString(),
                    exchange: item['buy'].toString(),
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: _priceBox(
                    label: 'Sell Price',
                    value: item['sellPrice'].toString(),
                    exchange: item['sell'].toString(),
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            Row(
              children: [
                Expanded(
                  child: _metricBox(
                    label: 'Est. Profit',
                    value: item['profit'].toString(),
                    color: AppColors.success,
                  ),
                ),
                const SizedBox(width: AppSpacing.sm),
                Expanded(
                  child: _metricBox(
                    label: 'AI Confidence',
                    value: item['confidence'].toString(),
                    color: color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.md),
            SizedBox(
              width: double.infinity,
              child: FilledButton(
                onPressed: null,
                style: FilledButton.styleFrom(
                  disabledBackgroundColor: color.withValues(alpha: 0.18),
                  disabledForegroundColor: color,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(AppSpacing.radius),
                  ),
                ),
                child: const Text('Execute Disabled - Phase 1 UI Only'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _priceBox({
    required String label,
    required String value,
    required String exchange,
  }) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.body.copyWith(fontSize: 12)),
          const SizedBox(height: AppSpacing.xs),
          Text(
            value,
            style: const TextStyle(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(exchange, style: AppTextStyles.body.copyWith(fontSize: 12)),
        ],
      ),
    );
  }

  Widget _metricBox({
    required String label,
    required String value,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.sm),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: AppTextStyles.body.copyWith(fontSize: 12)),
          const SizedBox(height: AppSpacing.xs),
          Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }
}
