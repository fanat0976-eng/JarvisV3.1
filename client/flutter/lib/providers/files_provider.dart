import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class FilesProvider extends ChangeNotifier {
  List<Map<String, dynamic>> _items = [];
  bool _loading = false;
  String _currentPath = 'workspace';
  ApiService? _api;

  List<Map<String, dynamic>> get items => _items;
  bool get loading => _loading;
  String get currentPath => _currentPath;

  void init(ApiService api) {
    _api = api;
  }

  Future<void> loadFiles({String? path}) async {
    if (_api == null) return;
    if (path != null) _currentPath = path;

    _loading = true;
    notifyListeners();

    try {
      _items = await _api!.getFiles(path: _currentPath);
    } catch (e) {
      debugPrint('Failed to load files: $e');
    } finally {
      _loading = false;
      notifyListeners();
    }
  }

  Future<String> readFile(String path) async {
    if (_api == null) return '';
    try {
      return await _api!.readFile(path);
    } catch (e) {
      return 'Ошибка чтения: $e';
    }
  }

  Future<void> writeFile(String path, String content) async {
    if (_api == null) return;
    try {
      await _api!.writeFile(path, content);
      await loadFiles();
    } catch (e) {
      debugPrint('Failed to write file: $e');
    }
  }

  void navigateTo(String path) {
    _currentPath = path;
    loadFiles();
  }

  void navigateUp() {
    final parts = _currentPath.split('/');
    if (parts.length > 1) {
      parts.removeLast();
      navigateTo(parts.join('/'));
    }
  }
}
