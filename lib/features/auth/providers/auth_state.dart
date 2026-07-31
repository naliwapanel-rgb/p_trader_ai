class AuthState {
  const AuthState({
    required this.isLoading,
    required this.isAuthenticated,
    this.errorMessage,
  });

  const AuthState.unauthenticated()
    : isLoading = false,
      isAuthenticated = false,
      errorMessage = null;

  const AuthState.loading()
    : isLoading = true,
      isAuthenticated = false,
      errorMessage = null;

  const AuthState.authenticated()
    : isLoading = false,
      isAuthenticated = true,
      errorMessage = null;

  const AuthState.failure(String message)
    : isLoading = false,
      isAuthenticated = false,
      errorMessage = message;

  final bool isLoading;
  final bool isAuthenticated;
  final String? errorMessage;
}
