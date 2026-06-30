import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../../domain/entities/crypto_asset.dart';
import '../../providers/market_providers.dart';
import 'market_details_screen.dart';
import 'market_search_screen.dart';
import '../watchlist/watchlist_screen.dart';
import '../../providers/watchlist_providers.dart';

class MarketsScreen extends ConsumerWidget {
  const MarketsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final marketsAsync = ref.watch(liveMarketsProvider);
    final selectedFilter = ref.watch(marketFilterProvider);
    final searchQuery = ref.watch(marketSearchProvider);
    final watchlistCount = ref.watch(watchlistProvider).value?.length ?? 0;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Markets'),
        actions: [
          IconButton(
            icon: Badge(
              isLabelVisible: watchlistCount > 0,
              label: Text('$watchlistCount'),
              child: const Icon(Icons.star),
            ),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const WatchlistScreen()),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.search),
            onPressed: () {
              final currentMarkets = ref.read(liveMarketsProvider).value;

              if (currentMarkets == null) return;

              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => MarketSearchScreen(coins: currentMarkets),
                ),
              );
            },
          ),
          IconButton(
            onPressed: () {
              ref.read(marketCacheServiceProvider).clear();
              ref.invalidate(liveMarketsProvider);
            },
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: marketsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.md),
            child: Text(
              'Failed to load live market data.\n$error',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.danger),
            ),
          ),
        ),
        data: (coins) {
          final filteredCoins = _applySearchAndFilter(
            coins,
            selectedFilter,
            searchQuery,
          );
          return RefreshIndicator(
            color: AppColors.primary,
            backgroundColor: AppColors.card,
            onRefresh: () async {
              ref.read(marketCacheServiceProvider).clear();
              ref.invalidate(liveMarketsProvider);
            },
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _searchBox(ref),
                  const SizedBox(height: AppSpacing.lg),
                  _marketSummary(coins),
                  const SizedBox(height: AppSpacing.lg),
                  _aiMarketBrief(coins),
                  const SizedBox(height: AppSpacing.lg),
                  _tabHeader(ref, selectedFilter),
                  const SizedBox(height: AppSpacing.md),
                  ...filteredCoins.map((coin) => _coinTile(context, coin)),
                  const SizedBox(height: AppSpacing.xl),
                ],
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _statusChip(String text, IconData icon, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),

      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(30),
      ),

      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, color: color, size: 18),

          const SizedBox(width: 6),

          Text(
            text,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _aiMarketBrief(List<CryptoAsset> coins) {
    final sortedByPerformance = [...coins]
      ..sort(
        (a, b) =>
            b.priceChangePercentage24h.compareTo(a.priceChangePercentage24h),
      );

    final best = sortedByPerformance.first;
    final worst = sortedByPerformance.last;

    final gainersCount = coins
        .where((coin) => coin.priceChangePercentage24h >= 0)
        .length;

    final sentiment = gainersCount >= coins.length * 0.6
        ? 'Bullish'
        : 'Cautious';

    final riskLevel =
        coins.any((coin) => coin.priceChangePercentage24h.abs() >= 8)
        ? 'High Risk'
        : 'Moderate Risk';

    final sentimentColor = sentiment == 'Bullish'
        ? AppColors.success
        : AppColors.warning;

    final riskColor = riskLevel == 'High Risk'
        ? AppColors.danger
        : Colors.orange;

    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.psychology, color: AppColors.primary),
              const SizedBox(width: AppSpacing.sm),
              Text('AI MARKET BRIEF', style: AppTextStyles.title),
            ],
          ),
          const SizedBox(height: AppSpacing.md),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _statusChip(
                sentiment,
                sentiment == 'Bullish' ? Icons.trending_up : Icons.shield,
                sentimentColor,
              ),
              _statusChip(riskLevel, Icons.security, riskColor),
              _statusChip('Live Data', Icons.wifi_tethering, AppColors.primary),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          Row(
            children: [
              Expanded(
                child: _marketInfo(
                  'Top Performer',
                  '${best.symbol.toUpperCase()} +${best.priceChangePercentage24h.toStringAsFixed(2)}%',
                  AppColors.success,
                ),
              ),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: _marketInfo(
                  'Weakest',
                  '${worst.symbol.toUpperCase()} ${worst.priceChangePercentage24h.toStringAsFixed(2)}%',
                  AppColors.danger,
                ),
              ),
            ],
          ),
          const SizedBox(height: AppSpacing.lg),
          Text(
            'Market sentiment is $sentiment. ${best.name} is leading the market, while ${worst.name} remains under pressure. Current risk level is $riskLevel based on 24h price movement across the top assets.',
            style: AppTextStyles.body,
          ),
        ],
      ),
    );
  }

  Widget _marketInfo(String title, String value, Color color) {
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
          Text(title, style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.xs),
          Text(
            value,
            style: TextStyle(color: color, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _searchBox(WidgetRef ref) {
    return TextField(
      onChanged: (value) {
        ref.read(marketSearchProvider.notifier).setQuery(value);
      },
      style: const TextStyle(color: AppColors.textPrimary),
      decoration: InputDecoration(
        hintText: 'Search coin or pair...',
        hintStyle: const TextStyle(color: AppColors.textSecondary),
        prefixIcon: const Icon(Icons.search, color: AppColors.primary),
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
          borderSide: const BorderSide(color: AppColors.primary),
        ),
      ),
    );
  }

  Widget _marketSummary(List<CryptoAsset> coins) {
    final totalMarketCap = coins.fold<double>(
      0,
      (sum, coin) => sum + coin.marketCap,
    );
    final totalVolume = coins.fold<double>(
      0,
      (sum, coin) => sum + coin.totalVolume,
    );

    return Row(
      children: [
        Expanded(
          child: _summaryCard(
            title: 'Market Cap',
            value: _formatLargeNumber(totalMarketCap),
            change: 'Top 50',
            icon: Icons.public,
            color: AppColors.primary,
          ),
        ),
        const SizedBox(width: AppSpacing.md),
        Expanded(
          child: _summaryCard(
            title: '24h Volume',
            value: _formatLargeNumber(totalVolume),
            change: 'Live',
            icon: Icons.bar_chart,
            color: AppColors.success,
          ),
        ),
      ],
    );
  }

  Widget _summaryCard({
    required String title,
    required String value,
    required String change,
    required IconData icon,
    required Color color,
  }) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            backgroundColor: color.withValues(alpha: 0.15),
            child: Icon(icon, color: color),
          ),
          const SizedBox(height: AppSpacing.md),
          Text(title, style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.xs),
          Text(value, style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.xs),
          Text(
            change,
            style: const TextStyle(
              color: AppColors.success,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _tabHeader(WidgetRef ref, MarketFilter selectedFilter) {
    return Row(
      children: [
        _chip(ref, 'All', MarketFilter.all, selectedFilter),
        const SizedBox(width: AppSpacing.sm),
        _chip(ref, 'Top Gainers', MarketFilter.gainers, selectedFilter),
        const SizedBox(width: AppSpacing.sm),
        _chip(ref, 'Top Losers', MarketFilter.losers, selectedFilter),
      ],
    );
  }

  Widget _chip(
    WidgetRef ref,
    String text,
    MarketFilter filter,
    MarketFilter selectedFilter,
  ) {
    final selected = filter == selectedFilter;

    return GestureDetector(
      onTap: () {
        ref.read(marketFilterProvider.notifier).setFilter(filter);
      },
      child: Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.md,
          vertical: AppSpacing.sm,
        ),
        decoration: BoxDecoration(
          color: selected
              ? AppColors.primary.withValues(alpha: 0.16)
              : AppColors.card,
          borderRadius: BorderRadius.circular(50),
          border: Border.all(
            color: selected ? AppColors.primary : AppColors.divider,
          ),
        ),
        child: Text(
          text,
          style: TextStyle(
            color: selected ? AppColors.primary : AppColors.textSecondary,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }

  Widget _coinTile(BuildContext context, CryptoAsset coin) {
    final isPositive = coin.priceChangePercentage24h >= 0;
    final changePrefix = isPositive ? '+' : '';

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radius),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => MarketDetailsScreen(coin: coin)),
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
                    Text(
                      '${coin.symbol.toUpperCase()}/USDT',
                      style: AppTextStyles.title,
                    ),
                    Text(coin.name, style: AppTextStyles.body),
                    const SizedBox(height: 4),
                    Text(
                      'Rank #${coin.marketCapRank} • Vol ${_formatLargeNumber(coin.totalVolume)}',
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.show_chart,
                color: isPositive ? AppColors.success : AppColors.danger,
              ),
              const SizedBox(width: AppSpacing.md),
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
                      color: isPositive ? AppColors.success : AppColors.danger,
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
  }

  List<CryptoAsset> _applySearchAndFilter(
    List<CryptoAsset> coins,
    MarketFilter filter,
    String query,
  ) {
    final normalizedQuery = query.trim().toLowerCase();

    List<CryptoAsset> result = coins;

    if (normalizedQuery.isNotEmpty) {
      result = result.where((coin) {
        return coin.name.toLowerCase().contains(normalizedQuery) ||
            coin.symbol.toLowerCase().contains(normalizedQuery);
      }).toList();
    }

    final sortedCoins = [...result];

    switch (filter) {
      case MarketFilter.gainers:
        sortedCoins.sort(
          (a, b) =>
              b.priceChangePercentage24h.compareTo(a.priceChangePercentage24h),
        );
        return sortedCoins;

      case MarketFilter.losers:
        sortedCoins.sort(
          (a, b) =>
              a.priceChangePercentage24h.compareTo(b.priceChangePercentage24h),
        );
        return sortedCoins;

      case MarketFilter.all:
        return result;
    }
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
