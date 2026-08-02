import '../data/exchange_account.dart';
import '../data/exchange_balance.dart';
import '../data/exchange_connection_result.dart';

abstract interface class ExchangeAccountRepository {
  Future<List<ExchangeAccount>> listAccounts();

  Future<ExchangeAccount> createAccount({
    required String exchangeName,
    required String accountName,
    required String apiKey,
    required String apiSecret,
    required bool isTestnet,
  });

  Future<ExchangeAccount> updateAccount({
    required int accountId,
    String? accountName,
    String? apiKey,
    String? apiSecret,
    bool? isTestnet,
    bool? isActive,
  });

  Future<void> deleteAccount(int accountId);

  Future<ExchangeConnectionResult> testConnection(int accountId);

  Future<ExchangeBalance> getBalance(int accountId);
}
