import 'dart:async';
import 'package:flutter/foundation.dart';
import '../models/message.dart';
import '../services/api_service.dart';
import 'package:provider/provider.dart';
import 'settings_provider.dart';

class ChatProvider extends ChangeNotifier {
  final List<Message> _messages = [];
  bool _isLoading = false;
  String _currentSessionId = '';
  ApiService? _api;

  List<Message> get messages => List.unmodifiable(_messages);
  bool get isLoading => _isLoading;
  String get sessionId => _currentSessionId;

  void init(ApiService api) {
    _api = api;
    _currentSessionId = 'ses_${DateTime.now().millisecondsSinceEpoch}';
  }

  Future<void> send(String text, {bool stream = true, bool useMemory = true}) async {
    if (_api == null || text.trim().isEmpty) return;

    _messages.add(Message.user(text));
    _isLoading = true;
    notifyListeners();

    try {
      if (stream) {
        await _sendStreaming(text, useMemory);
      } else {
        await _sendNormal(text, useMemory);
      }
    } catch (e) {
      _messages.add(Message.assistant('Ошибка: $e'));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  Future<void> _sendNormal(String text, bool useMemory) async {
    final result = await _api!.chat(_messages, useMemory: useMemory);
    final reply = result['reply'] ?? '';
    final toolResults = result['tool_results'];

    _messages.add(Message.assistant(
      reply,
      toolResults: toolResults != null
          ? List<Map<String, dynamic>>.from(toolResults)
          : null,
    ));
  }

  Future<void> _sendStreaming(String text, bool useMemory) async {
    final streamMsg = Message.assistant('', isStreaming: true);
    _messages.add(streamMsg);
    final index = _messages.length - 1;

    String fullText = '';
    await for (final chunk in _api!.chatStream(_messages.sublist(0, _messages.length - 1), useMemory: useMemory)) {
      fullText += chunk;
      _messages[index] = Message.assistant(fullText, isStreaming: true);
      notifyListeners();
    }

    _messages[index] = Message.assistant(fullText, isStreaming: false);
  }

  Future<void> sendAgent(String text, {int maxIterations = 3}) async {
    if (_api == null || text.trim().isEmpty) return;

    _messages.add(Message.user(text));
    _isLoading = true;
    notifyListeners();

    try {
      final result = await _api!.agent(_messages, maxIterations: maxIterations);
      final reply = result['reply'] ?? '';
      final toolResults = result['tool_results'];
      final iterations = result['iterations'] ?? 0;

      _messages.add(Message.assistant(
        '$reply\n\n_(${iterations} итераций)_',
        toolResults: toolResults != null
            ? List<Map<String, dynamic>>.from(toolResults)
            : null,
      ));
    } catch (e) {
      _messages.add(Message.assistant('Ошибка агента: $e'));
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  void clear() {
    _messages.clear();
    _currentSessionId = 'ses_${DateTime.now().millisecondsSinceEpoch}';
    notifyListeners();
  }
}
