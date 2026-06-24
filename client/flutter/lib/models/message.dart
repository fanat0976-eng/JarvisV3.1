class Message {
  final String role;
  final String content;
  final DateTime timestamp;
  final bool isStreaming;
  final List<Map<String, dynamic>>? toolResults;

  Message({
    required this.role,
    required this.content,
    DateTime? timestamp,
    this.isStreaming = false,
    this.toolResults,
  }) : timestamp = timestamp ?? DateTime.now();

  Message copyWith({
    String? content,
    bool? isStreaming,
    List<Map<String, dynamic>>? toolResults,
  }) {
    return Message(
      role: role,
      content: content ?? this.content,
      timestamp: timestamp,
      isStreaming: isStreaming ?? this.isStreaming,
      toolResults: toolResults ?? this.toolResults,
    );
  }

  Map<String, dynamic> toApi() => {
    'role': role,
    'content': content,
  };

  factory Message.user(String text) => Message(role: 'user', content: text);
  factory Message.assistant(String text, {bool isStreaming = false, List<Map<String, dynamic>>? toolResults}) =>
      Message(role: 'assistant', content: text, isStreaming: isStreaming, toolResults: toolResults);
}
