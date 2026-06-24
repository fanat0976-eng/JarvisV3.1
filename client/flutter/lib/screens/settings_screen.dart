import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import '../providers/settings_provider.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final settings = context.watch<SettingsProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Настройки')),
      body: ListView(
        children: [
          const _SectionHeader('Подключение'),
          ListTile(
            leading: const Icon(Icons.dns),
            title: const Text('Сервер'),
            subtitle: Text(settings.serverUrl),
            onTap: () => _editServerUrl(context, settings),
          ),
          ListTile(
            leading: const Icon(Icons.key),
            title: const Text('Auth Key'),
            subtitle: Text(settings.authKey),
            onTap: () => _editAuthKey(context, settings),
          ),
          const Divider(),
          const _SectionHeader('Интерфейс'),
          SwitchListTile(
            secondary: const Icon(Icons.dark_mode),
            title: const Text('Тёмная тема'),
            value: settings.darkMode,
            onChanged: (_) => settings.toggleDarkMode(),
          ),
          const Divider(),
          const _SectionHeader('Голос'),
          ListTile(
            leading: const Icon(Icons.record_voice_over),
            title: const Text('Голос'),
            subtitle: Text(settings.voice),
            onTap: () => _selectVoice(context, settings),
          ),
          SwitchListTile(
            secondary: const Icon(Icons.volume_up),
            title: const Text('Авто-озвучка ответов'),
            value: settings.autoTts,
            onChanged: (_) => settings.toggleAutoTts(),
          ),
          const Divider(),
          const _SectionHeader('Community Plugins'),
          _CommunityPluginsSection(),
          const Divider(),
          const _SectionHeader('О приложении'),
          const ListTile(
            leading: Icon(Icons.info_outline),
            title: Text('J.A.R.V.I.S V3.1'),
            subtitle: Text('AI OS — Mobile Client'),
          ),
        ],
      ),
    );
  }

  void _editServerUrl(BuildContext context, SettingsProvider settings) {
    final ctrl = TextEditingController(text: settings.serverUrl);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('URL сервера'),
        content: TextField(controller: ctrl, decoration: const InputDecoration(hintText: 'http://10.0.2.2:8003')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Отмена')),
          FilledButton(
            onPressed: () {
              settings.setServerUrl(ctrl.text.trim());
              Navigator.pop(ctx);
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  void _editAuthKey(BuildContext context, SettingsProvider settings) {
    final ctrl = TextEditingController(text: settings.authKey);
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Auth Key'),
        content: TextField(controller: ctrl),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Отмена')),
          FilledButton(
            onPressed: () {
              settings.setAuthKey(ctrl.text.trim());
              Navigator.pop(ctx);
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  void _selectVoice(BuildContext context, SettingsProvider settings) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text('Выберите голос', style: TextStyle(fontWeight: FontWeight.w600)),
            ),
            ListTile(
              leading: const Icon(Icons.person),
              title: const Text('Дмитрий'),
              subtitle: const Text('ru-RU-DmitryNeural'),
              trailing: settings.voice == 'dmitry' ? const Icon(Icons.check, color: Colors.blue) : null,
              onTap: () {
                settings.setVoice('dmitry');
                Navigator.pop(ctx);
              },
            ),
            ListTile(
              leading: const Icon(Icons.person_outline),
              title: const Text('Светлана'),
              subtitle: const Text('ru-RU-SvetlanaNeural'),
              trailing: settings.voice == 'svetlana' ? const Icon(Icons.check, color: Colors.blue) : null,
              onTap: () {
                settings.setVoice('svetlana');
                Navigator.pop(ctx);
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _CommunityPluginsSection extends StatefulWidget {
  @override
  State<_CommunityPluginsSection> createState() => _CommunityPluginsSectionState();
}

class _CommunityPluginsSectionState extends State<_CommunityPluginsSection> {
  List<dynamic> _plugins = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final settings = context.read<SettingsProvider>();
    try {
      final r = await http.get(
        Uri.parse('${settings.serverUrl}/plugins/community'),
        headers: settings.headers,
      );
      final data = json.decode(r.body);
      setState(() {
        _plugins = data['plugins'] ?? [];
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator()));
    if (_plugins.isEmpty) return const Padding(padding: EdgeInsets.all(16), child: Text('Нет community-плагинов', style: TextStyle(color: Colors.grey)));
    return Column(
      children: _plugins.map((p) => ListTile(
        leading: Icon(Icons.extension, color: p['loaded'] == true ? Colors.green : Colors.grey),
        title: Text(p['name'] ?? ''),
        subtitle: Text(p['description'] ?? '', maxLines: 1, overflow: TextOverflow.ellipsis),
        trailing: Text('v${p['version']}', style: const TextStyle(fontSize: 12)),
      )).toList(),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader(this.title);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 4),
      child: Text(
        title.toUpperCase(),
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }
}
