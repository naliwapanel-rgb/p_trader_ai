import 'package:logger/logger.dart';

class AppLogger {
  static final Logger instance = Logger(
    printer: PrettyPrinter(methodCount: 0, errorMethodCount: 5, lineLength: 80),
  );
}
