import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/files_provider.dart';

class FilesScreen extends StatefulWidget {
  const FilesScreen({super.key});

  @override
  State<FilesScreen> createState() => _FilesScreenState();
}

class _FilesScreenState extends State<FilesScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<FilesProvider>().loadFiles();
    });
  }

  @override
  Widget build(BuildContext context) {
    final files = context.watch<FilesProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text(files.currentPath),
        leading: files.currentPath != 'workspace'
            ? IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () => files.navigateUp(),
              )
            : null,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => files.loadFiles(),
          ),
        ],
      ),
      body: files.loading
          ? const Center(child: CircularProgressIndicator())
          : files.items.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.folder_open, size: 64, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text('Папка пуста', style: TextStyle(color: Colors.grey[500], fontSize: 16)),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: () => files.loadFiles(),
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    itemCount: files.items.length,
                    itemBuilder: (ctx, i) {
                      final item = files.items[i];
                      final isDir = item['is_dir'] == true;
                      final name = item['name'] ?? '';
                      final size = item['size'] ?? 0;

                      return ListTile(
                        leading: Icon(
                          isDir ? Icons.folder : Icons.insert_drive_file,
                          color: isDir ? Colors.amber : Colors.grey,
                        ),
                        title: Text(name),
                        subtitle: isDir ? null : Text(_formatSize(size), style: const TextStyle(fontSize: 12)),
                        trailing: isDir ? const Icon(Icons.chevron_right) : null,
                        onTap: () {
                          if (isDir) {
                            files.navigateTo(item['path']);
                          } else {
                            _showFileContent(context, item['path'], name);
                          }
                        },
                      );
                    },
                  ),
                ),
    );
  }

  String _formatSize(int bytes) {
    if (bytes < 1024) return '$bytes B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)} KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
  }

  void _showFileContent(BuildContext context, String path, String name) async {
    final files = context.read<FilesProvider>();
    final content = await files.readFile(path);

    if (!context.mounted) return;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.3,
        maxChildSize: 0.95,
        expand: false,
        builder: (ctx, scrollController) => Column(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Expanded(child: Text(name, style: const TextStyle(fontWeight: FontWeight.w600))),
                  IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.pop(ctx)),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: SingleChildScrollView(
                controller: scrollController,
                padding: const EdgeInsets.all(16),
                child: SelectableText(content, style: const TextStyle(fontFamily: 'monospace', fontSize: 13)),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
