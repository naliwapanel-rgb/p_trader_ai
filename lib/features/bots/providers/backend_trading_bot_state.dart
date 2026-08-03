import '../data/backend_trading_bot.dart';

class BackendTradingBotState {
  const BackendTradingBotState({
    required this.bots,
    required this.busyBotIds,
    required this.isLoading,
    required this.isMutating,
    required this.hasLoaded,
    this.errorMessage,
    this.infoMessage,
  });

  const BackendTradingBotState.initial()
    : bots = const <BackendTradingBot>[],
      busyBotIds = const <int>{},
      isLoading = false,
      isMutating = false,
      hasLoaded = false,
      errorMessage = null,
      infoMessage = null;

  final List<BackendTradingBot> bots;
  final Set<int> busyBotIds;
  final bool isLoading;
  final bool isMutating;
  final bool hasLoaded;
  final String? errorMessage;
  final String? infoMessage;

  List<BackendTradingBot> get activeBots {
    return bots.where((bot) => bot.status.isActive).toList(growable: false);
  }

  List<BackendTradingBot> get runningBots {
    return bots
        .where(
          (bot) =>
              bot.status == TradingBotStatus.running ||
              bot.status == TradingBotStatus.starting,
        )
        .toList(growable: false);
  }

  List<BackendTradingBot> get pausedBots {
    return bots
        .where((bot) => bot.status == TradingBotStatus.paused)
        .toList(growable: false);
  }

  BackendTradingBot? findById(int botId) {
    for (final bot in bots) {
      if (bot.id == botId) {
        return bot;
      }
    }

    return null;
  }

  bool isBotBusy(int botId) {
    return busyBotIds.contains(botId);
  }

  BackendTradingBotState copyWith({
    List<BackendTradingBot>? bots,
    Set<int>? busyBotIds,
    bool? isLoading,
    bool? isMutating,
    bool? hasLoaded,
    String? errorMessage,
    String? infoMessage,
    bool clearError = false,
    bool clearInfo = false,
  }) {
    return BackendTradingBotState(
      bots: bots ?? this.bots,
      busyBotIds: busyBotIds ?? this.busyBotIds,
      isLoading: isLoading ?? this.isLoading,
      isMutating: isMutating ?? this.isMutating,
      hasLoaded: hasLoaded ?? this.hasLoaded,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
      infoMessage: clearInfo ? null : infoMessage ?? this.infoMessage,
    );
  }
}
