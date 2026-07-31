class AuthUser {
  const AuthUser({
    required this.id,
    required this.fullName,
    required this.email,
    required this.isActive,
    required this.createdAt,
  });

  final int id;
  final String fullName;
  final String email;
  final bool isActive;
  final DateTime createdAt;

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    final id = json['id'];
    final fullName = json['full_name'];
    final email = json['email'];
    final isActive = json['is_active'];
    final createdAt = json['created_at'];

    if (id is! int || id <= 0) {
      throw const FormatException('User response contained an invalid ID.');
    }

    if (fullName is! String || fullName.trim().isEmpty) {
      throw const FormatException(
        'User response contained an invalid full name.',
      );
    }

    if (email is! String || email.trim().isEmpty) {
      throw const FormatException(
        'User response contained an invalid email address.',
      );
    }

    if (isActive is! bool) {
      throw const FormatException(
        'User response contained an invalid account status.',
      );
    }

    if (createdAt is! String) {
      throw const FormatException(
        'User response contained an invalid creation date.',
      );
    }

    final parsedCreatedAt = DateTime.tryParse(createdAt);

    if (parsedCreatedAt == null) {
      throw const FormatException(
        'User response contained an invalid creation date.',
      );
    }

    return AuthUser(
      id: id,
      fullName: fullName.trim(),
      email: email.trim(),
      isActive: isActive,
      createdAt: parsedCreatedAt,
    );
  }
}
