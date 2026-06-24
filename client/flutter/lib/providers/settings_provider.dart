import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsProvider extends ChangeNotifier {
  String _serverUrl = 'http://10.0.2.2:8003';
  String _authKey = 'jarvis-v3.1';
  bool _darkMode = true;
  String _voice = 'dmitry';
  bool _autoTts = false;

  String get serverUrl => _serverUrl;
  String get authKey => _authKey;
  bool get darkMode => _darkMode;
  String get voice => _voice;
  bool get autoTts => _autoTts;

  Map<String, String> get headers => {
    'X-Auth-Key': _authKey,
    'Content-Type': 'application/json',
  };

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _serverUrl = prefs.getString('server_url') ?? 'http://10.0.2.2:8003';
    _authKey = prefs.getString('auth_key') ?? 'jarvis-v3.1';
    _darkMode = prefs.getBool('dark_mode') ?? true;
    _voice = prefs.getString('voice') ?? 'dmitry';
    _autoTts = prefs.getBool('auto_tts') ?? false;
    notifyListeners();
  }

  Future<void> _save() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('server_url', _serverUrl);
    await prefs.setString('auth_key', _authKey);
    await prefs.setBool('dark_mode', _darkMode);
    await prefs.setString('voice', _voice);
    await prefs.setBool('auto_tts', _autoTts);
  }

  Future<void> setServerUrl(String url) async {
    _serverUrl = url;
    await _save();
    notifyListeners();
  }

  Future<void> setAuthKey(String key) async {
    _authKey = key;
    await _save();
    notifyListeners();
  }

  Future<void> toggleDarkMode() async {
    _darkMode = !_darkMode;
    await _save();
    notifyListeners();
  }

  Future<void> setVoice(String v) async {
    _voice = v;
    await _save();
    notifyListeners();
  }

  Future<void> toggleAutoTts() async {
    _autoTts = !_autoTts;
    await _save();
    notifyListeners();
  }

  String get wsUrl {
    final http = _serverUrl.replaceFirst('http://', 'ws://');
    return '$http/android/ws';
  }
}
