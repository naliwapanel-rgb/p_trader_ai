import '../domain/exchange_account_repository.dart';
import 'exchange_account.dart';
import 'exchange_account_remote_data_source.dart';
import 'exchange_balance.dart';
import 'exchange_connection_result.dart';

class ExchangeAccountRepositoryImpl implements ExchangeAccountRepository {
  const ExchangeAccountRepositoryImpl({
    required ExchangeAccountRemoteDataSource remoteDataSource,
  }) : _remoteDataSource = remoteDataSource;

  final ExchangeAccountRemoteDataSource _remoteDataSource;

  @override
  Future<List<ExchangeAccount>> listAccounts() {
    return _remoteDataSource.listAccounts();
  }

  @override
  Future<ExchangeAccount> createAccount({
    required String exchangeName,
    required String accountName,
    required String apiKey,
    required String apiSecret,
    required bool isTestnet,
  }) {
    return _remoteDataSource.createAccount(
      exchangeName: exchangeName,
      accountName: accountName,
      apiKey: apiKey,
      apiSecret: apiSecret,
      isTestnet: isTestnet,
    );
  }

  @override
  Future<ExchangeAccount> updateAccount({
    required int accountId,
    String? accountName,
    String? apiKey,
    String? apiSecret,
    bool? isTestnet,
    bool? isActive,
  }) {
    return _remoteDataSource.updateAccount(
      accountId: accountId,
      accountName: accountName,
      apiKey: apiKey,
      apiSecret: apiSecret,
      isTestnet: isTestnet,
      isActive: isActive,
    );
  }

  @override
  Future<void> deleteAccount(int accountId) {
    return _remoteDataSource.deleteAccount(accountId);
  }

  @override
  Future<ExchangeConnectionResult> testConnection(int accountId) {
    return _remoteDataSource.testConnection(accountId);
  }

  @override
  Future<ExchangeBalance> getBalance(int accountId) {
    return _remoteDataSource.getBalance(accountId);
  }
}
