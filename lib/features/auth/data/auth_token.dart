class AuthToken {
  const AuthToken({required this.accessToken, required this.tokenType});

  final String accessToken;
  final String tokenType;

  factory AuthToken.fromJson(Map<String, dynamic> json) {
    final accessToken = json['access_token'];
    final tokenType = json['token_type'] ?? 'bearer';

    if (accessToken is! String || accessToken.trim().isEmpty) {
      throw const FormatException(
        'Authentication response did not contain an access token.',
      );
    }

    if (tokenType is! String || tokenType.trim().isEmpty) {
      throw const FormatException(
        'Authentication response contained an invalid token type.',
      );
    }

    return AuthToken(
      accessToken: accessToken.trim(),
      tokenType: tokenType.trim().toLowerCase(),
    );
  }
}
