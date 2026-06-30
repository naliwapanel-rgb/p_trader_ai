import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../../providers/market_providers.dart';
import '../../providers/watchlist_providers.dart';
import '../markets/market_details_screen.dart';

class WatchlistScreen extends ConsumerWidget {
  const WatchlistScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final marketsAsync = ref.watch(liveMarketsProvider);
    final watchlistAsync = ref.watch(watchlistProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Watchlist')),
      body: marketsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => Center(
          child: Text(
            'Failed to load watchlist.\n$error',
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.danger),
          ),
        ),
        data: (coins) {
          final ids = watchlistAsync.value ?? [];
          final watchlistCoins = coins
              .where((coin) => ids.contains(coin.id))
              .toList();

          if (watchlistCoins.isEmpty) {
            return _emptyState();
          }

          return ListView.builder(
            padding: const EdgeInsets.all(AppSpacing.md),
            itemCount: watchlistCoins.length,
            itemBuilder: (context, index) {
              final coin = watchlistCoins[index];
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
                                '${coin.symbol.toUpperCase()}/USDT',
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
                        IconButton(
                          onPressed: () {
                            ref
                                .read(watchlistProvider.notifier)
                                .toggle(coin.id);
                          },
                          icon: const Icon(Icons.star, color: Colors.amber),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }

  Widget _emptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: GlassCard(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.star_border, size: 72, color: Colors.amber),
              const SizedBox(height: AppSpacing.md),
              Text('No favorites yet', style: AppTextStyles.title),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'Open a coin and tap the star icon to add it to your watchlist.',
                textAlign: TextAlign.center,
                style: AppTextStyles.body,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
