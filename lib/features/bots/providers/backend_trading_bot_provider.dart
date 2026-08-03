import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/backend_trading_bot.dart';
import '../data/trading_bot_remote_data_source.dart';
import '../data/trading_bot_repository_impl.dart';
import '../domain/trading_bot_repository.dart';
import 'backend_trading_bot_state.dart';

final backendTradingBotRemoteDataSourceProvider =
    Provider<TradingBotRemoteDataSource>((ref) {
      return DioTradingBotRemoteDataSource(
        ref.watch(backendDioClientProvider).dio,
      );
    });

final backendTradingBotRepositoryProvider = Provider<TradingBotRepository>((
  ref,
) {
  return TradingBotRepositoryImpl(
    remoteDataSource: ref.watch(backendTradingBotRemoteDataSourceProvider),
  );
});

final backendTradingBotProvider =
    NotifierProvider<BackendTradingBotNotifier, BackendTradingBotState>(
      BackendTradingBotNotifier.new,
    );

class BackendTradingBotNotifier extends Notifier<BackendTradingBotState> {
  @override
  BackendTradingBotState build() {
    return const BackendTradingBotState.initial();
  }

  Future<void> loadBots({TradingBotStatus? status}) async {
    if (state.isLoading) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearInfo: true);

    try {
      final bots = await ref
          .read(backendTradingBotRepositoryProvider)
          .listBots(status: status);

      state = state.copyWith(
        bots: _sortedBots(bots),
        isLoading: false,
        hasLoaded: true,
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(
        isLoading: false,
        hasLoaded: true,
        errorMessage: error.message,
      );
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        hasLoaded: true,
        errorMessage: 'Trading bots could not be loaded.',
      );
    }
  }

  Future<BackendTradingBot?> createBot(TradingBotCreateRequest request) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      final bot = await ref
          .read(backendTradingBotRepositoryProvider)
          .createBot(request);

      state = state.copyWith(
        bots: _sortedBots(<BackendTradingBot>[...state.bots, bot]),
        isMutating: false,
        hasLoaded: true,
        infoMessage: 'Trading bot created successfully.',
        clearError: true,
      );

      return bot;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The trading bot could not be created.',
      );
      return null;
    }
  }

  Future<BackendTradingBot?> updateBot({
    required int botId,
    required TradingBotUpdateRequest request,
  }) async {
    if (state.isBotBusy(botId)) {
      return null;
    }

    _setBotBusy(botId, true);

    try {
      final bot = await ref
          .read(backendTradingBotRepositoryProvider)
          .updateBot(botId: botId, request: request);

      state = state.copyWith(
        bots: _replaceBot(bot),
        busyBotIds: _withoutBusyBot(botId),
        infoMessage: 'Trading bot updated successfully.',
        clearError: true,
      );

      return bot;
    } on AppException catch (error) {
      state = state.copyWith(
        busyBotIds: _withoutBusyBot(botId),
        errorMessage: error.message,
      );
      return null;
    } catch (_) {
      state = state.copyWith(
        busyBotIds: _withoutBusyBot(botId),
        errorMessage: 'The trading bot could not be updated.',
      );
      return null;
    }
  }

  Future<bool> deleteBot(int botId) async {
    if (state.isBotBusy(botId)) {
      return false;
    }

    _setBotBusy(botId, true);

    try {
      await ref.read(backendTradingBotRepositoryProvider).deleteBot(botId);

      state = state.copyWith(
        bots: state.bots
            .where((bot) => bot.id != botId)
            .toList(growable: false),
        busyBotIds: _withoutBusyBot(botId),
        infoMessage: 'Trading bot deleted successfully.',
        clearError: true,
      );

      return true;
    } on AppException catch (error) {
      state = state.copyWith(
        busyBotIds: _withoutBusyBot(botId),
        errorMessage: error.message,
      );
      return false;
    } catch (_) {
      state = state.copyWith(
        busyBotIds: _withoutBusyBot(botId),
        errorMessage: 'The trading bot could not be deleted.',
      );
      return false;
    }
  }

  Future<TradingBotLifecycleResult?> performLifecycle({
    required int botId,
    required TradingBotLifecycleAction action,
  }) async {
    if (state.isBotBusy(botId)) {
      return null;
    }

    _setBotBusy(botId, true);

    try {
      final result = await ref
          .read(backendTradingBotRepositoryProvider)
          .performLifecycle(botId: botId, action: action);

      state = state.copyWith(
        bots: _replaceBot(result.bot),
        busyBotIds: _withoutBusyBot(botId),
        infoMessage: result.changed
            ? _lifecycleSuccessMessage(action)
            : 'The trading bot was already '
                  '${result.status.backendValue.toLowerCase()}.',
        clearError: true,
      );

      return result;
    } on AppException catch (error) {
      state = state.copyWith(
        busyBotIds: _withoutBusyBot(botId),
        errorMessage: error.message,
      );
      return null;
    } catch (_) {
      state = state.copyWith(
        busyBotIds: _withoutBusyBot(botId),
        errorMessage: 'The trading-bot action could not be completed.',
      );
      return null;
    }
  }

  void clearMessages() {
    state = state.copyWith(clearError: true, clearInfo: true);
  }

  void _setBotBusy(int botId, bool busy) {
    final busyIds = Set<int>.from(state.busyBotIds);

    if (busy) {
      busyIds.add(botId);
    } else {
      busyIds.remove(botId);
    }

    state = state.copyWith(
      busyBotIds: Set<int>.unmodifiable(busyIds),
      clearError: true,
      clearInfo: true,
    );
  }

  Set<int> _withoutBusyBot(int botId) {
    final busyIds = Set<int>.from(state.busyBotIds)..remove(botId);

    return Set<int>.unmodifiable(busyIds);
  }

  List<BackendTradingBot> _replaceBot(BackendTradingBot replacement) {
    final bots = state.bots
        .map((bot) => bot.id == replacement.id ? replacement : bot)
        .toList(growable: false);

    final exists = bots.any((bot) => bot.id == replacement.id);

    if (!exists) {
      return _sortedBots(<BackendTradingBot>[...bots, replacement]);
    }

    return _sortedBots(bots);
  }

  List<BackendTradingBot> _sortedBots(Iterable<BackendTradingBot> bots) {
    final sorted = bots.toList();

    sorted.sort((first, second) => second.createdAt.compareTo(first.createdAt));

    return List<BackendTradingBot>.unmodifiable(sorted);
  }

  String _lifecycleSuccessMessage(TradingBotLifecycleAction action) {
    return switch (action) {
      TradingBotLifecycleAction.prepare => 'Trading bot prepared successfully.',
      TradingBotLifecycleAction.start => 'Trading bot started successfully.',
      TradingBotLifecycleAction.pause => 'Trading bot paused successfully.',
      TradingBotLifecycleAction.resume => 'Trading bot resumed successfully.',
      TradingBotLifecycleAction.stop => 'Trading bot stopped successfully.',
    };
  }
}
