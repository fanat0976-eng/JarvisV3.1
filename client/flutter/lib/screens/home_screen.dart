import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/settings_provider.dart';
import '../providers/chat_provider.dart';
import '../providers/memory_provider.dart';
import '../providers/files_provider.dart';
import '../services/api_service.dart';
import 'chat_screen.dart';
import 'memory_screen.dart';
import 'files_screen.dart';
import 'settings_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  ApiService? _api;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _reconnect();
      context.read<SettingsProvider>().addListener(_onSettingsChanged);
    });
  }

  @override
  void dispose() {
    context.read<SettingsProvider>().removeListener(_onSettingsChanged);
    super.dispose();
  }

  void _onSettingsChanged() {
    _reconnect();
  }

  void _reconnect() {
    final settings = context.read<SettingsProvider>();
    _api = ApiService(baseUrl: settings.serverUrl, headers: settings.headers);

    context.read<ChatProvider>().init(_api!);
    context.read<MemoryProvider>().init(_api!);
    context.read<FilesProvider>().init(_api!);
  }

  @override
  Widget build(BuildContext context) {
    final screens = [
      const ChatScreen(),
      const MemoryScreen(),
      const FilesScreen(),
      const SettingsScreen(),
    ];

    return Scaffold(
      body: screens[_currentIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (i) => setState(() => _currentIndex = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.chat_bubble_outline), selectedIcon: Icon(Icons.chat_bubble), label: 'Чат'),
          NavigationDestination(icon: Icon(Icons.psychology_outlined), selectedIcon: Icon(Icons.psychology), label: 'Память'),
          NavigationDestination(icon: Icon(Icons.folder_outlined), selectedIcon: Icon(Icons.folder), label: 'Файлы'),
          NavigationDestination(icon: Icon(Icons.settings_outlined), selectedIcon: Icon(Icons.settings), label: 'Настройки'),
        ],
      ),
    );
  }
}
