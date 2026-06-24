import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/memory_provider.dart';

class MemoryScreen extends StatefulWidget {
  const MemoryScreen({super.key});

  @override
  State<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends State<MemoryScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<MemoryProvider>().loadFacts();
    });
  }

  @override
  Widget build(BuildContext context) {
    final memory = context.watch<MemoryProvider>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Память'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => memory.loadFacts(),
          ),
        ],
      ),
      body: memory.loading
          ? const Center(child: CircularProgressIndicator())
          : memory.facts.isEmpty
              ? Center(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.psychology_outlined, size: 64, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text('Память пуста', style: TextStyle(color: Colors.grey[500], fontSize: 16)),
                      const SizedBox(height: 8),
                      Text('Факты извлекаются автоматически\nили добавляются вручную', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey[500], fontSize: 13)),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(8),
                  itemCount: memory.facts.length,
                  itemBuilder: (ctx, i) {
                    final fact = memory.facts[i];
                    return Card(
                      margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 4),
                      child: ListTile(
                        leading: CircleAvatar(
                          child: Text((fact['key'] ?? '?')[0].toUpperCase()),
                        ),
                        title: Text(fact['key'] ?? '', style: const TextStyle(fontWeight: FontWeight.w500)),
                        subtitle: Text(fact['value'] ?? '', maxLines: 2, overflow: TextOverflow.ellipsis),
                        trailing: Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            if (fact['confidence'] != null)
                              Padding(
                                padding: const EdgeInsets.only(right: 8),
                                child: Text('${((fact['confidence'] as num) * 100).round()}%', style: const TextStyle(fontSize: 12)),
                              ),
                            IconButton(
                              icon: const Icon(Icons.delete_outline, size: 20),
                              onPressed: () => _confirmDelete(context, fact['key']),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddDialog(context),
        child: const Icon(Icons.add),
      ),
    );
  }

  void _showAddDialog(BuildContext context) {
    final keyCtrl = TextEditingController();
    final valueCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Добавить факт'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: keyCtrl, decoration: const InputDecoration(labelText: 'Ключ')),
            const SizedBox(height: 12),
            TextField(controller: valueCtrl, decoration: const InputDecoration(labelText: 'Значение')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Отмена')),
          FilledButton(
            onPressed: () {
              if (keyCtrl.text.isNotEmpty && valueCtrl.text.isNotEmpty) {
                context.read<MemoryProvider>().addFact(keyCtrl.text, valueCtrl.text);
                Navigator.pop(ctx);
              }
            },
            child: const Text('Добавить'),
          ),
        ],
      ),
    );
  }

  void _confirmDelete(BuildContext context, String? key) {
    if (key == null) return;
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Удалить факт?'),
        content: Text('Удалить "$key"?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Отмена')),
          FilledButton(
            onPressed: () {
              context.read<MemoryProvider>().deleteFact(key);
              Navigator.pop(ctx);
            },
            child: const Text('Удалить'),
          ),
        ],
      ),
    );
  }
}
