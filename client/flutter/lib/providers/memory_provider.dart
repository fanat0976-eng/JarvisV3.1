import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class MemoryProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _facts = [];
  bool _loading = false;
  ApiService? _api;

  List<Map<String, dynamic>> get facts => _facts;
  bool get loading => _loading;

  void init(ApiService api) {
    _api = api;
  }

  Future<void> loadFacts({String entity = 'user'}) async {
    if (_api == null) return;
    _loading = true;
    notifyListeners();

    try {
      _facts = await _api!.getFacts(entity: entity);
    } catch (e) {
      debugPrint('Failed to load facts: $e');
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<void> addFact(String key, String value, {String entity = 'user'}) async {
    if (_api == null) return;
    try {
      await _api!.addFact(key, value, entity: entity);
      await loadFacts(entity: entity);
    } catch (e) {
      debugPrint('Failed to add fact: $e');
    }
  }

  Future<void> deleteFact(String key, {String entity = 'user'}) async {
    if (_api == null) return;
    try {
      await _api!.deleteFact(key, entity: entity);
      await loadFacts(entity: entity);
    } catch (e) {
      debugPrint('Failed to delete fact: $e');
    }
  }
}
