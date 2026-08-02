import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/app_spacing.dart';
import '../../core/theme/app_text_styles.dart';
import '../../core/widgets/glass_card.dart';
import '../../domain/entities/crypto_asset.dart';
import '../../providers/market_providers.dart';
import '../markets/market_details_screen.dart';
import 'data/backend_watchlist_item.dart';
import 'providers/backend_watchlist_provider.dart';
import 'providers/backend_watchlist_state.dart';

class WatchlistScreen extends ConsumerStatefulWidget {
  const WatchlistScreen({super.key});

  @override
  ConsumerState<WatchlistScreen> createState() {
    return _WatchlistScreenState();
  }
}

class _WatchlistScreenState extends ConsumerState<WatchlistScreen> {
  @override
  void initState() {
    super.initState();

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) {
        return;
      }

      ref.read(backendWatchlistProvider.notifier).loadItems();
    });
  }

  Future<void> _refresh() async {
    ref.read(marketCacheServiceProvider).clear();

    final marketRefresh = ref.refresh(liveMarketsProvider.future);

    final watchlistRefresh = ref
        .read(backendWatchlistProvider.notifier)
        .loadItems(force: true);

    await Future.wait<Object?>([marketRefresh, watchlistRefresh]);
  }

  @override
  Widget build(BuildContext context) {
    final marketsAsync = ref.watch(liveMarketsProvider);

    final watchlistState = ref.watch(backendWatchlistProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Watchlist'),
        actions: [
          IconButton(
            onPressed: watchlistState.isLoading
                ? null
                : () {
                    _refresh();
                  },
            tooltip: 'Refresh watchlist',
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: _body(marketsAsync, watchlistState),
    );
  }

  Widget _body(
    AsyncValue<List<CryptoAsset>> marketsAsync,
    BackendWatchlistState watchlistState,
  ) {
    if (watchlistState.isLoading && !watchlistState.hasLoaded) {
      return const Center(child: CircularProgressIndicator());
    }

    if (watchlistState.errorMessage != null && !watchlistState.hasLoaded) {
      return _errorState(watchlistState.errorMessage!);
    }

    return marketsAsync.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) {
        return _errorState(
          'Failed to load current market data.\n'
          '$error',
        );
      },
      data: (coins) {
        return _watchlistBody(coins, watchlistState);
      },
    );
  }

  Widget _watchlistBody(List<CryptoAsset> coins, BackendWatchlistState state) {
    final items = state.itemsForExchange(WatchlistSymbolMapper.defaultExchange);

    if (items.isEmpty) {
      return _emptyState();
    }

    final coinsBySymbol = <String, CryptoAsset>{
      for (final coin in coins) coin.symbol.trim().toUpperCase(): coin,
    };

    final entries = <_WatchlistMarketEntry>[];
    var unavailableCount = 0;

    for (final item in items) {
      final coin = coinsBySymbol[item.baseAssetSymbol];

      if (coin == null) {
        unavailableCount += 1;
        continue;
      }

      entries.add(_WatchlistMarketEntry(item: item, coin: coin));
    }

    return RefreshIndicator(
      color: AppColors.primary,
      backgroundColor: AppColors.card,
      onRefresh: _refresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.md),
        children: [
          if (state.errorMessage != null) ...[
            _messageCard(
              state.errorMessage!,
              AppColors.warning,
              Icons.warning_amber_outlined,
            ),
            const SizedBox(height: AppSpacing.md),
          ],
          if (unavailableCount > 0) ...[
            _messageCard(
              unavailableCount == 1
                  ? 'One saved asset is not '
                        'available in the current '
                        'market feed.'
                  : '$unavailableCount saved assets '
                        'are not available in the '
                        'current market feed.',
              AppColors.warning,
              Icons.cloud_off_outlined,
            ),
            const SizedBox(height: AppSpacing.md),
          ],
          if (entries.isEmpty)
            _unavailableState()
          else
            ...entries.map((entry) => _watchlistCard(entry, state.isMutating)),
        ],
      ),
    );
  }

  Widget _watchlistCard(_WatchlistMarketEntry entry, bool isMutating) {
    final item = entry.item;
    final coin = entry.coin;

    final isPositive = coin.priceChangePercentage24h >= 0;

    final changePrefix = isPositive ? '+' : '';

    return Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: InkWell(
        borderRadius: BorderRadius.circular(AppSpacing.radius),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute<void>(
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
                      '${coin.symbol.toUpperCase()}'
                      '/USDT',
                      style: AppTextStyles.body,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      item.exchange,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                      ),
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
                    '$changePrefix'
                    '${coin.priceChangePercentage24h.toStringAsFixed(2)}%',
                    style: TextStyle(
                      color: isPositive ? AppColors.success : AppColors.danger,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
              IconButton(
                onPressed: isMutating
                    ? null
                    : () {
                        _removeItem(item, coin);
                      },
                tooltip: 'Remove from watchlist',
                icon: const Icon(Icons.star, color: Colors.amber),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _removeItem(BackendWatchlistItem item, CryptoAsset coin) async {
    final removed = await ref
        .read(backendWatchlistProvider.notifier)
        .deleteItem(item.id);

    if (!mounted) {
      return;
    }

    if (!removed) {
      final message =
          ref.read(backendWatchlistProvider).errorMessage ??
          'The watchlist item could not be removed.';

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(message)));

      return;
    }

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('${coin.name} removed from watchlist.')),
    );
  }

  Widget _errorState(String message) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          const SizedBox(height: 120),
          const Icon(
            Icons.cloud_off_outlined,
            size: 64,
            color: AppColors.danger,
          ),
          const SizedBox(height: AppSpacing.md),
          Text(message, textAlign: TextAlign.center, style: AppTextStyles.body),
          const SizedBox(height: AppSpacing.md),
          Center(
            child: FilledButton.icon(
              onPressed: () {
                _refresh();
              },
              icon: const Icon(Icons.refresh),
              label: const Text('Try Again'),
            ),
          ),
        ],
      ),
    );
  }

  Widget _emptyState() {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.lg),
        children: [
          const SizedBox(height: 100),
          GlassCard(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.star_border, size: 72, color: Colors.amber),
                const SizedBox(height: AppSpacing.md),
                Text('No favorites yet', style: AppTextStyles.title),
                const SizedBox(height: AppSpacing.sm),
                Text(
                  'Open a coin and tap the star '
                  'icon to add it to your '
                  'authenticated watchlist.',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.body,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _unavailableState() {
    return GlassCard(
      child: Column(
        children: [
          const Icon(Icons.query_stats, size: 56, color: AppColors.warning),
          const SizedBox(height: AppSpacing.md),
          Text('Saved assets unavailable', style: AppTextStyles.title),
          const SizedBox(height: AppSpacing.sm),
          Text(
            'Your watchlist is saved, but '
            'its assets are not included in '
            'the current CoinGecko market feed.',
            textAlign: TextAlign.center,
            style: AppTextStyles.body,
          ),
        ],
      ),
    );
  }

  Widget _messageCard(String message, Color color, IconData icon) {
    return GlassCard(
      child: Row(
        children: [
          Icon(icon, color: color),
          const SizedBox(width: AppSpacing.md),
          Expanded(child: Text(message, style: AppTextStyles.body)),
        ],
      ),
    );
  }
}

class _WatchlistMarketEntry {
  const _WatchlistMarketEntry({required this.item, required this.coin});

  final BackendWatchlistItem item;
  final CryptoAsset coin;
}
