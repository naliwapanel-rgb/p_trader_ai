import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:p_trader_ai/core/errors/app_exception.dart';
import 'package:p_trader_ai/features/exchange_accounts/data/exchange_account.dart';
import 'package:p_trader_ai/features/exchange_accounts/data/exchange_balance.dart';
import 'package:p_trader_ai/features/exchange_accounts/data/exchange_connection_result.dart';
import 'package:p_trader_ai/features/exchange_accounts/domain/exchange_account_repository.dart';
import 'package:p_trader_ai/features/exchange_accounts/providers/exchange_account_provider.dart';

void main() {
  group('ExchangeAccountNotifier', () {
    test('loads exchange accounts', () async {
      final repository = _FakeRepository(
        accounts: <ExchangeAccount>[_account()],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(exchangeAccountProvider.notifier).loadAccounts();

      final state = container.read(exchangeAccountProvider);

      expect(repository.listCalls, 1);
      expect(state.accounts, hasLength(1));
      expect(state.errorMessage, isNull);
    });

    test('creates and appends an account', () async {
      final repository = _FakeRepository();
      final container = _container(repository);
      addTearDown(container.dispose);

      final account = await container
          .read(exchangeAccountProvider.notifier)
          .createAccount(
            exchangeName: 'BYBIT',
            accountName: 'Main',
            apiKey: 'key-value',
            apiSecret: 'secret-value',
            isTestnet: false,
          );

      expect(account, isNotNull);
      expect(repository.createCalls, 1);
      expect(container.read(exchangeAccountProvider).accounts, hasLength(1));
    });

    test('updates an existing account', () async {
      final repository = _FakeRepository(
        accounts: <ExchangeAccount>[_account()],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(exchangeAccountProvider.notifier).loadAccounts();

      await container
          .read(exchangeAccountProvider.notifier)
          .updateAccount(
            accountId: 4,
            accountName: 'Updated',
            isTestnet: true,
            isActive: false,
          );

      final account = container.read(exchangeAccountProvider).accounts.single;

      expect(repository.updateCalls, 1);
      expect(account.accountName, 'Updated');
      expect(account.isActive, isFalse);
    });

    test('deletes an account from state', () async {
      final repository = _FakeRepository(
        accounts: <ExchangeAccount>[_account()],
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(exchangeAccountProvider.notifier).loadAccounts();

      final deleted = await container
          .read(exchangeAccountProvider.notifier)
          .deleteAccount(4);

      expect(deleted, isTrue);
      expect(repository.deleteCalls, 1);
      expect(container.read(exchangeAccountProvider).accounts, isEmpty);
    });

    test('returns connection result', () async {
      final repository = _FakeRepository();
      final container = _container(repository);
      addTearDown(container.dispose);

      final result = await container
          .read(exchangeAccountProvider.notifier)
          .testConnection(4);

      expect(result?.appearsConnected, isTrue);
      expect(repository.testCalls, 1);
    });

    test('returns normalized balance', () async {
      final repository = _FakeRepository();
      final container = _container(repository);
      addTearDown(container.dispose);

      final balance = await container
          .read(exchangeAccountProvider.notifier)
          .getBalance(4);

      expect(balance?.totalEquityUsd, 100);
      expect(repository.balanceCalls, 1);
    });

    test('stores repository error message', () async {
      final repository = _FakeRepository(
        listError: const AppException('Unable to load accounts'),
      );

      final container = _container(repository);
      addTearDown(container.dispose);

      await container.read(exchangeAccountProvider.notifier).loadAccounts();

      expect(
        container.read(exchangeAccountProvider).errorMessage,
        'Unable to load accounts',
      );
    });
  });
}

ProviderContainer _container(ExchangeAccountRepository repository) {
  return ProviderContainer(
    overrides: [
      exchangeAccountRepositoryProvider.overrideWithValue(repository),
    ],
  );
}

ExchangeAccount _account({
  String accountName = 'Main',
  bool isTestnet = false,
  bool isActive = true,
}) {
  return ExchangeAccount(
    id: 4,
    userId: 7,
    exchangeName: 'BYBIT',
    accountName: accountName,
    isTestnet: isTestnet,
    isActive: isActive,
    createdAt: DateTime.utc(2026, 8, 1),
  );
}

class _FakeRepository implements ExchangeAccountRepository {
  _FakeRepository({this.accounts = const <ExchangeAccount>[], this.listError});

  final List<ExchangeAccount> accounts;
  final AppException? listError;

  int listCalls = 0;
  int createCalls = 0;
  int updateCalls = 0;
  int deleteCalls = 0;
  int testCalls = 0;
  int balanceCalls = 0;

  @override
  Future<List<ExchangeAccount>> listAccounts() async {
    listCalls += 1;

    if (listError != null) {
      throw listError!;
    }

    return accounts;
  }

  @override
  Future<ExchangeAccount> createAccount({
    required String exchangeName,
    required String accountName,
    required String apiKey,
    required String apiSecret,
    required bool isTestnet,
  }) async {
    createCalls += 1;

    return _account(accountName: accountName, isTestnet: isTestnet);
  }

  @override
  Future<ExchangeAccount> updateAccount({
    required int accountId,
    String? accountName,
    String? apiKey,
    String? apiSecret,
    bool? isTestnet,
    bool? isActive,
  }) async {
    updateCalls += 1;

    return _account(
      accountName: accountName ?? 'Main',
      isTestnet: isTestnet ?? false,
      isActive: isActive ?? true,
    );
  }

  @override
  Future<void> deleteAccount(int accountId) async {
    deleteCalls += 1;
  }

  @override
  Future<ExchangeConnectionResult> testConnection(int accountId) async {
    testCalls += 1;

    return const ExchangeConnectionResult(
      data: <String, dynamic>{'connected': true},
    );
  }

  @override
  Future<ExchangeBalance> getBalance(int accountId) async {
    balanceCalls += 1;

    return const ExchangeBalance(
      accountType: 'UNIFIED',
      totalEquityUsd: 100,
      totalWalletBalanceUsd: 90,
      totalAvailableBalanceUsd: 80,
      totalUnrealizedPnlUsd: 10,
      coins: <ExchangeCoinBalance>[],
    );
  }
}
