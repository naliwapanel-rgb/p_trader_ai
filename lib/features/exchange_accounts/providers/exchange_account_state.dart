import '../data/exchange_account.dart';

class ExchangeAccountState {
  const ExchangeAccountState({
    required this.isLoading,
    required this.isMutating,
    required this.accounts,
    this.errorMessage,
  });

  const ExchangeAccountState.initial()
    : isLoading = false,
      isMutating = false,
      accounts = const <ExchangeAccount>[],
      errorMessage = null;

  final bool isLoading;
  final bool isMutating;
  final List<ExchangeAccount> accounts;
  final String? errorMessage;

  ExchangeAccountState copyWith({
    bool? isLoading,
    bool? isMutating,
    List<ExchangeAccount>? accounts,
    String? errorMessage,
    bool clearError = false,
  }) {
    return ExchangeAccountState(
      isLoading: isLoading ?? this.isLoading,
      isMutating: isMutating ?? this.isMutating,
      accounts: accounts ?? this.accounts,
      errorMessage: clearError ? null : errorMessage ?? this.errorMessage,
    );
  }
}
