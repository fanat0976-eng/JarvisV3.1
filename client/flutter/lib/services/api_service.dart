import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/message.dart';

class ApiService {
  final String baseUrl;
  final Map<String, String> headers;

  ApiService({required this.baseUrl, required this.headers});

  Future<Map<String, dynamic>> health() async {
    final r = await http.get(
      Uri.parse('$baseUrl/health'),
      headers: headers,
    );
    return json.decode(r.body);
  }

  Future<Map<String, dynamic>> chat(List<Message> messages,
      {bool useMemory = true}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/brain/chat'),
      headers: headers,
      body: json.encode({
        'messages': messages.map((m) => m.toApi()).toList(),
        'use_memory': useMemory,
      }),
    );
    return json.decode(r.body);
  }

  Stream<String> chatStream(List<Message> messages,
      {bool useMemory = true}) async* {
    final request = http.Request(
      'POST',
      Uri.parse('$baseUrl/brain/chat/stream'),
    );
    request.headers.addAll(headers);
    request.body = json.encode({
      'messages': messages.map((m) => m.toApi()).toList(),
      'use_memory': useMemory,
    });

    final response = await http.Client().send(request);
    String buffer = '';

    await for (final chunk in response.stream.transform(utf8.decoder)) {
      buffer += chunk;
      final lines = buffer.split('\n');
      buffer = lines.removeLast();

      for (final line in lines) {
        if (line.startsWith('data: ')) {
          final data = line.substring(6).trim();
          if (data == '[DONE]') return;
          try {
            final json = jsonDecode(data);
            if (json['content'] != null) {
              yield json['content'];
            }
          } catch (_) {}
        }
      }
    }
  }

  Future<Map<String, dynamic>> agent(List<Message> messages,
      {int maxIterations = 3}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/brain/agent'),
      headers: headers,
      body: json.encode({
        'messages': messages.map((m) => m.toApi()).toList(),
        'max_iterations': maxIterations,
      }),
    );
    return json.decode(r.body);
  }

  Future<List<Map<String, dynamic>>> getFacts({String entity = 'user'}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/memory_v2/facts/get'),
      headers: headers,
      body: json.encode({'entity': entity}),
    );
    final data = json.decode(r.body);
    return List<Map<String, dynamic>>.from(data['facts'] ?? []);
  }

  Future<void> addFact(String key, String value,
      {String entity = 'user'}) async {
    await http.post(
      Uri.parse('$baseUrl/memory_v2/facts'),
      headers: headers,
      body: json.encode({
        'entity': entity,
        'key': key,
        'value': value,
      }),
    );
  }

  Future<void> deleteFact(String key, {String entity = 'user'}) async {
    await http.post(
      Uri.parse('$baseUrl/memory_v2/facts/delete'),
      headers: headers,
      body: json.encode({
        'entity': entity,
        'key': key,
      }),
    );
  }

  Future<List<Map<String, dynamic>>> getFiles({String path = 'workspace'}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/files/ls'),
      headers: headers,
      body: json.encode({'path': path}),
    );
    final data = json.decode(r.body);
    return List<Map<String, dynamic>>.from(data['items'] ?? []);
  }

  Future<String> readFile(String path) async {
    final r = await http.post(
      Uri.parse('$baseUrl/files/read'),
      headers: headers,
      body: json.encode({'path': path}),
    );
    final data = json.decode(r.body);
    return data['text'] ?? '';
  }

  Future<void> writeFile(String path, String content) async {
    await http.post(
      Uri.parse('$baseUrl/files/write'),
      headers: headers,
      body: json.encode({'path': path, 'content': content}),
    );
  }

  Future<Map<String, dynamic>> speak(String text,
      {String voice = 'dmitry'}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/tts_bridge/speak'),
      headers: headers,
      body: json.encode({'text': text, 'voice': voice}),
    );
    return json.decode(r.body);
  }

  String audioUrl(String filename) => '$baseUrl/tts_bridge/audio/$filename';
}
