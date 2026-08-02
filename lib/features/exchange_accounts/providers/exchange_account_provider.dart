import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/errors/app_exception.dart';
import '../../../core/providers/backend_network_provider.dart';
import '../data/exchange_account.dart';
import '../data/exchange_account_remote_data_source.dart';
import '../data/exchange_account_repository_impl.dart';
import '../data/exchange_balance.dart';
import '../data/exchange_connection_result.dart';
import '../domain/exchange_account_repository.dart';
import 'exchange_account_state.dart';

final exchangeAccountRemoteDataSourceProvider =
    Provider<ExchangeAccountRemoteDataSource>((ref) {
      return DioExchangeAccountRemoteDataSource(
        ref.watch(backendDioClientProvider),
      );
    });

final exchangeAccountRepositoryProvider = Provider<ExchangeAccountRepository>((
  ref,
) {
  return ExchangeAccountRepositoryImpl(
    remoteDataSource: ref.watch(exchangeAccountRemoteDataSourceProvider),
  );
});

final exchangeAccountProvider =
    NotifierProvider<ExchangeAccountNotifier, ExchangeAccountState>(
      ExchangeAccountNotifier.new,
    );

class ExchangeAccountNotifier extends Notifier<ExchangeAccountState> {
  @override
  ExchangeAccountState build() {
    return const ExchangeAccountState.initial();
  }

  Future<void> loadAccounts() async {
    if (state.isLoading) {
      return;
    }

    state = state.copyWith(isLoading: true, clearError: true);

    try {
      final accounts = await ref
          .read(exchangeAccountRepositoryProvider)
          .listAccounts();

      state = state.copyWith(
        isLoading: false,
        accounts: accounts,
        clearError: true,
      );
    } on AppException catch (error) {
      state = state.copyWith(isLoading: false, errorMessage: error.message);
    } catch (_) {
      state = state.copyWith(
        isLoading: false,
        errorMessage: 'Exchange accounts could not be loaded.',
      );
    }
  }

  Future<ExchangeAccount?> createAccount({
    required String exchangeName,
    required String accountName,
    required String apiKey,
    required String apiSecret,
    required bool isTestnet,
  }) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true);

    try {
      final account = await ref
          .read(exchangeAccountRepositoryProvider)
          .createAccount(
            exchangeName: exchangeName,
            accountName: accountName,
            apiKey: apiKey,
            apiSecret: apiSecret,
            isTestnet: isTestnet,
          );

      state = state.copyWith(
        isMutating: false,
        accounts: <ExchangeAccount>[...state.accounts, account],
        clearError: true,
      );

      return account;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The exchange account could not be created.',
      );
      return null;
    }
  }

  Future<ExchangeAccount?> updateAccount({
    required int accountId,
    required String accountName,
    String? apiKey,
    String? apiSecret,
    required bool isTestnet,
    required bool isActive,
  }) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true);

    try {
      final account = await ref
          .read(exchangeAccountRepositoryProvider)
          .updateAccount(
            accountId: accountId,
            accountName: accountName,
            apiKey: apiKey,
            apiSecret: apiSecret,
            isTestnet: isTestnet,
            isActive: isActive,
          );

      final accounts = state.accounts
          .map((existing) => existing.id == account.id ? account : existing)
          .toList(growable: false);

      state = state.copyWith(
        isMutating: false,
        accounts: accounts,
        clearError: true,
      );

      return account;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The exchange account could not be updated.',
      );
      return null;
    }
  }

  Future<bool> deleteAccount(int accountId) async {
    if (state.isMutating) {
      return false;
    }

    state = state.copyWith(isMutating: true, clearError: true);

    try {
      await ref
          .read(exchangeAccountRepositoryProvider)
          .deleteAccount(accountId);

      state = state.copyWith(
        isMutating: false,
        accounts: state.accounts
            .where((account) => account.id != accountId)
            .toList(growable: false),
        clearError: true,
      );

      return true;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return false;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The exchange account could not be deleted.',
      );
      return false;
    }
  }

  Future<ExchangeConnectionResult?> testConnection(int accountId) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true);

    try {
      final result = await ref
          .read(exchangeAccountRepositoryProvider)
          .testConnection(accountId);

      state = state.copyWith(isMutating: false, clearError: true);

      return result;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The exchange connection test failed.',
      );
      return null;
    }
  }

  Future<ExchangeBalance?> getBalance(int accountId) async {
    if (state.isMutating) {
      return null;
    }

    state = state.copyWith(isMutating: true, clearError: true);

    try {
      final balance = await ref
          .read(exchangeAccountRepositoryProvider)
          .getBalance(accountId);

      state = state.copyWith(isMutating: false, clearError: true);

      return balance;
    } on AppException catch (error) {
      state = state.copyWith(isMutating: false, errorMessage: error.message);
      return null;
    } catch (_) {
      state = state.copyWith(
        isMutating: false,
        errorMessage: 'The exchange balance could not be loaded.',
      );
      return null;
    }
  }

  void clearError() {
    state = state.copyWith(clearError: true);
  }
}
