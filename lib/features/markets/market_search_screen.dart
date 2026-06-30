import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../../domain/entities/crypto_asset.dart';
import 'market_details_screen.dart';

class MarketSearchScreen extends StatefulWidget {
  final List<CryptoAsset> coins;

  const MarketSearchScreen({super.key, required this.coins});

  @override
  State<MarketSearchScreen> createState() => _MarketSearchScreenState();
}

class _MarketSearchScreenState extends State<MarketSearchScreen> {
  String query = '';

  @override
  Widget build(BuildContext context) {
    final results = _filteredCoins();

    return Scaffold(
      appBar: AppBar(title: const Text('Search Markets')),
      body: Padding(
        padding: const EdgeInsets.all(AppSpacing.md),
        child: Column(
          children: [
            _premiumSearchBox(),
            const SizedBox(height: AppSpacing.lg),
            _quickFilters(),
            const SizedBox(height: AppSpacing.lg),
            Expanded(
              child: results.isEmpty ? _emptyState() : _resultsList(results),
            ),
          ],
        ),
      ),
    );
  }

  Widget _premiumSearchBox() {
    return TextField(
      autofocus: true,
      onChanged: (value) {
        setState(() {
          query = value;
        });
      },
      style: const TextStyle(color: AppColors.textPrimary),
      decoration: InputDecoration(
        hintText: 'Search BTC, ETH, SOL...',
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        prefixIcon: const Icon(Icons.search, color: AppColors.primary),
        suffixIcon: query.isEmpty
            ? null
            : IconButton(
                onPressed: () {
                  setState(() {
                    query = '';
                  });
                },
                icon: const Icon(Icons.close, color: AppColors.textSecondary),
              ),
        filled: true,
        fillColor: AppColors.card,
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
          borderSide: const BorderSide(color: AppColors.primary, width: 1.4),
        ),
      ),
    );
  }

  Widget _quickFilters() {
    return Row(
      children: [
        _quickChip('BTC'),
        const SizedBox(width: AppSpacing.sm),
        _quickChip('ETH'),
        const SizedBox(width: AppSpacing.sm),
        _quickChip('SOL'),
        const SizedBox(width: AppSpacing.sm),
        _quickChip('BNB'),
      ],
    );
  }

  Widget _quickChip(String text) {
    return GestureDetector(
      onTap: () {
        setState(() {
          query = text;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: BoxDecoration(
          color: AppColors.primary.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(50),
          border: Border.all(color: AppColors.primary.withValues(alpha: 0.4)),
        ),
        child: Text(
          text,
          style: const TextStyle(
            color: AppColors.primary,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _resultsList(List<CryptoAsset> coins) {
    return ListView.builder(
      itemCount: coins.length,
      itemBuilder: (context, index) {
        final coin = coins[index];
        final isPositive = coin.priceChangePercentage24h >= 0;
        final changePrefix = isPositive ? '+' : '';

        return Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.sm),
          child: InkWell(
            borderRadius: BorderRadius.circular(AppSpacing.radius),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => MarketDetailsScreen(coin: coin),
                ),
              );
            },
            child: GlassCard(
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: AppColors.card,
                    backgroundImage: NetworkImage(coin.image),
                  ),
                  const SizedBox(width: AppSpacing.md),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(coin.name, style: AppTextStyles.title),
                        Text(
                          '${coin.symbol.toUpperCase()}/USDT • Rank #${coin.marketCapRank}',
                          style: AppTextStyles.body,
                        ),
                      ],
                    ),
                  ),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text(
                        '\$${coin.currentPrice.toStringAsFixed(coin.currentPrice < 1 ? 4 : 2)}',
                        style: AppTextStyles.title,
                      ),
                      Text(
                        '$changePrefix${coin.priceChangePercentage24h.toStringAsFixed(2)}%',
                        style: TextStyle(
                          color: isPositive
                              ? AppColors.success
                              : AppColors.danger,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _emptyState() {
    return Center(child: Text('No market found', style: AppTextStyles.body));
  }

  List<CryptoAsset> _filteredCoins() {
    final normalizedQuery = query.trim().toLowerCase();

    if (normalizedQuery.isEmpty) {
      return widget.coins.take(20).toList();
    }

    return widget.coins.where((coin) {
      return coin.name.toLowerCase().contains(normalizedQuery) ||
          coin.symbol.toLowerCase().contains(normalizedQuery);
    }).toList();
  }
}
