import '../data/auth_user.dart';

class AuthState {
  const AuthState({
    required this.isLoading,
    required this.isAuthenticated,
    this.user,
    this.errorMessage,
  });

  const AuthState.unauthenticated()
    : isLoading = false,
      isAuthenticated = false,
      user = null,
      errorMessage = null;

  const AuthState.loading()
    : isLoading = true,
      isAuthenticated = false,
      user = null,
      errorMessage = null;

  const AuthState.authenticated(AuthUser authenticatedUser)
    : isLoading = false,
      isAuthenticated = true,
      user = authenticatedUser,
      errorMessage = null;

  const AuthState.failure(String message)
    : isLoading = false,
      isAuthenticated = false,
      user = null,
      errorMessage = message;

  final bool isLoading;
  final bool isAuthenticated;
  final AuthUser? user;
  final String? errorMessage;
}
