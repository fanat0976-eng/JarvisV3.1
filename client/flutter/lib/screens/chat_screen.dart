import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/chat_provider.dart';
import '../providers/settings_provider.dart';
import '../models/message.dart';
import '../widgets/message_bubble.dart';
import '../widgets/typing_indicator.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final _controller = TextEditingController();
  final _scrollController = ScrollController();
  bool _agentMode = false;

  void _send() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    final chat = context.read<ChatProvider>();
    if (_agentMode) {
      chat.sendAgent(text);
    } else {
      chat.send(text);
    }

    _controller.clear();
    _scrollToBottom();
  }

  void _toggleVoice() {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Голосовой ввод будет доступен в следующей версии')),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final chat = context.watch<ChatProvider>();
    final settings = context.watch<SettingsProvider>();

    if (chat.messages.isEmpty) {
      context.select<ChatProvider, int>((p) => p.messages.length);
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('J.A.R.V.I.S', style: TextStyle(fontWeight: FontWeight.w600)),
        actions: [
          if (_agentMode)
            const Padding(
              padding: EdgeInsets.only(right: 8),
              child: Chip(label: Text('Агент', style: TextStyle(fontSize: 12)), visualDensity: VisualDensity.compact),
            ),
          IconButton(
            icon: const Icon(Icons.delete_outline),
            onPressed: () => _showClearDialog(context),
            tooltip: 'Очистить',
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: chat.messages.isEmpty
                ? _buildWelcome(context)
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    itemCount: chat.messages.length + (chat.isLoading ? 1 : 0),
                    itemBuilder: (ctx, i) {
                      if (i == chat.messages.length) {
                        return const TypingIndicator();
                      }
                      return MessageBubble(message: chat.messages[i]);
                    },
                  ),
          ),
          _buildInputBar(context),
        ],
      ),
    );
  }

  Widget _buildWelcome(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.psychology, size: 80, color: Theme.of(context).colorScheme.primary.withAlpha(80)),
          const SizedBox(height: 16),
          Text('Привет! Я Jarvis.', style: Theme.of(context).textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text('Задайте вопрос или включите режим агента', style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey)),
          const SizedBox(height: 24),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            alignment: WrapAlignment.center,
            children: [
              _quickChip('Расскажи анекдот'),
              _quickChip('Покажи файлы'),
              _quickChip('Что ты умеешь?'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _quickChip(String text) {
    return ActionChip(
      label: Text(text, style: const TextStyle(fontSize: 13)),
      onPressed: () {
        _controller.text = text;
        _send();
      },
    );
  }

  Widget _buildInputBar(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
      decoration: BoxDecoration(
        color: Theme.of(context).scaffoldBackgroundColor,
        border: Border(top: BorderSide(color: Colors.grey.withAlpha(30))),
      ),
      child: SafeArea(
        top: false,
        child: Row(
          children: [
            IconButton(
              icon: Icon(_agentMode ? Icons.smart_toy : Icons.smart_toy_outlined),
              onPressed: () => setState(() => _agentMode = !_agentMode),
              tooltip: _agentMode ? 'Режим чата' : 'Режим агента',
              color: _agentMode ? Theme.of(context).colorScheme.primary : null,
            ),
            const SizedBox(width: 4),
            Expanded(
              child: TextField(
                controller: _controller,
                maxLines: 4,
                minLines: 1,
                textInputAction: TextInputAction.send,
                onSubmitted: (_) => _send(),
                decoration: const InputDecoration(hintText: 'Сообщение...'),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: const Icon(Icons.mic),
              onPressed: _toggleVoice,
              tooltip: 'Голос',
            ),
            const SizedBox(width: 4),
            IconButton.filled(
              onPressed: context.read<ChatProvider>().isLoading ? null : _send,
              icon: const Icon(Icons.send, size: 20),
            ),
          ],
        ),
      ),
    );
  }

  void _showClearDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Очистить чат?'),
        content: const Text('Все сообщения будут удалены'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Отмена')),
          FilledButton(
            onPressed: () {
              context.read<ChatProvider>().clear();
              Navigator.pop(ctx);
            },
            child: const Text('Очистить'),
          ),
        ],
      ),
    );
  }
}
