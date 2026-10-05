import 'package:speech_to_text/speech_to_text.dart';

/// El plugin se inicializa una vez; las pantallas registran su callback actual.
class ReportesVoice {
  static final speech = SpeechToText();
  static Object? _owner;
  static void Function()? _error;
  static void Function(String)? _status;

  static Future<bool> initialize(Object owner, void Function() error, void Function(String) status) async {
    _owner = owner; _error = error; _status = status;
    return speech.initialize(onError: (_) => _error?.call(), onStatus: (s) => _status?.call(s));
  }

  static void release(Object owner) {
    if (_owner == owner) { _owner = null; _error = null; _status = null; speech.cancel(); }
  }
}
