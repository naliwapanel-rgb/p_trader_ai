import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/backend_price_alert.dart';
import '../data/backend_price_alert_repository_impl.dart';
import '../data/price_alert_remote_data_source.dart';
import '../domain/backend_price_alert_repository.dart';
import 'backend_price_alert_state.dart';

final backendPriceAlertRemoteDataSourceProvider =
    Provider<PriceAlertRemoteDataSource>((ref) {
      return DioPriceAlertRemoteDataSource(
        ref.watch(backendDioClientProvider).dio,
      );
    });

final backendPriceAlertRepositoryProvider =
    Provider<BackendPriceAlertRepository>((ref) {
      return BackendPriceAlertRepositoryImpl(
        remoteDataSource: ref.watch(backendPriceAlertRemoteDataSourceProvider),
      );
    });

final backendPriceAlertProvider =
    NotifierProvider<BackendPriceAlertNotifier, BackendPriceAlertState>(
      BackendPriceAlertNotifier.new,
    );

class BackendPriceAlertNotifier extends Notifier<BackendPriceAlertState> {
  @override
  BackendPriceAlertState build() {
    return const BackendPriceAlertState.initial();
  }

  Future<void> loadAlerts({bool force = false}) async {
    if (state.isLoading || (state.hasLoaded && !force)) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true, clearInfo: true);

    try {
      final alerts = await ref
          .read(backendPriceAlertRepositoryProvider)
          .listAlerts();

      state = state.copyWith(
        alerts: _sorted(alerts),
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
        errorMessage: 'Price alerts could not be loaded.',
      );
    }
  }

  Future<BackendPriceAlert?> createAlert({
    required String symbol,
    String exchange = PriceAlertSymbolMapper.defaultExchange,
    required BackendPriceAlertCondition condition,
    required double targetPrice,
  }) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      final created = await ref
          .read(backendPriceAlertRepositoryProvider)
          .createAlert(
            symbol: symbol,
            exchange: exchange,
            condition: condition,
            targetPrice: targetPrice,
          );

      state = state.copyWith(
        alerts: _sorted(<BackendPriceAlert>[...state.alerts, created]),
        isMutating: false,
        hasLoaded: true,
        infoMessage: 'Price alert created.',
        clearError: true,
      );

      return created;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The price alert could not be created.',
      );
      return null;
    }
  }

  Future<BackendPriceAlert?> updateAlert({
    required int alertId,
    String? symbol,
    String? exchange,
    BackendPriceAlertCondition? condition,
    double? targetPrice,
    bool? isEnabled,
    bool? triggered,
  }) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      final updated = await ref
          .read(backendPriceAlertRepositoryProvider)
          .updateAlert(
            alertId: alertId,
            symbol: symbol,
            exchange: exchange,
            condition: condition,
            targetPrice: targetPrice,
            isEnabled: isEnabled,
            triggered: triggered,
          );

      final alerts = state.alerts
          .map((alert) => alert.id == updated.id ? updated : alert)
          .toList(growable: false);

      final exists = alerts.any((alert) => alert.id == updated.id);

      state = state.copyWith(
        alerts: _sorted(
          exists ? alerts : <BackendPriceAlert>[...alerts, updated],
        ),
        isMutating: false,
        hasLoaded: true,
        infoMessage: 'Price alert updated.',
        clearError: true,
      );

      return updated;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The price alert could not be updated.',
      );
      return null;
    }
  }

  Future<BackendPriceAlert?> toggleEnabled(int alertId) async {
    final existing = state.findById(alertId);

    if (existing == null) {
      state = state.copyWith(
        errorMessage: 'Price alert not found.',
        clearInfo: true,
      );
      return null;
    }

    return updateAlert(alertId: alertId, isEnabled: !existing.isEnabled);
  }

  Future<BackendPriceAlert?> resetTriggered(int alertId) async {
    return updateAlert(alertId: alertId, triggered: false);
  }

  Future<bool> deleteAlert(int alertId) async {
    if (state.isMutating) {
      return false;
    }

    state = state.copyWith(isMutating: true, clearError: true, clearInfo: true);

    try {
      await ref.read(backendPriceAlertRepositoryProvider).deleteAlert(alertId);

      state = state.copyWith(
        alerts: state.alerts
            .where((alert) => alert.id != alertId)
            .toList(growable: false),
        isMutating: false,
        hasLoaded: true,
        infoMessage: 'Price alert deleted.',
        clearError: true,
      );

      return true;
    } on AppException catch (error) {
      if (error.statusCode == 404) {
        state = state.copyWith(
          alerts: state.alerts
              .where((alert) => alert.id != alertId)
              .toList(growable: false),
          isMutating: false,
          hasLoaded: true,
          infoMessage: 'Price alert was already deleted.',
          clearError: true,
        );

        return true;
      }

      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return false;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The price alert could not be deleted.',
      );
      return false;
    }
  }

  void clearMessages() {
    state = state.copyWith(clearError: true, clearInfo: true);
  }

  List<BackendPriceAlert> _sorted(List<BackendPriceAlert> alerts) {
    final sorted = List<BackendPriceAlert>.of(alerts);

    sorted.sort((left, right) => right.createdAt.compareTo(left.createdAt));

    return List<BackendPriceAlert>.unmodifiable(sorted);
  }
}
