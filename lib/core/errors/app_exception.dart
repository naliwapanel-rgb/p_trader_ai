class AppException implements Exception {
  final String message;
  final int? statusCode;

  const AppException(this.message, {this.statusCode});

  @override
  String toString() {
    return 'AppException(message: $message, statusCode: $statusCode)';
  }
}
