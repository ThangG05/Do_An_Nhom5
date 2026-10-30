import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'api_client.dart';
import 'app_config.dart';

class ChatRealtime {
  ChatRealtime(this._api);
  final ApiClient _api;
  WebSocketChannel? _channel;
  StreamSubscription? _subscription;

  Future<void> connect(void Function(Map<String, dynamic> event) onEvent) async {
    await close();
    final ticket = await _api.postAuthenticated('/chat/ws-ticket', {});
    final value = ticket['ticket']?.toString();
    if (value == null || value.isEmpty) return;
    final base = AppConfig.apiBaseUrl.replaceFirst(RegExp(r'^http'), 'ws');
    _channel = WebSocketChannel.connect(Uri.parse('$base/chat/ws?ticket=$value'));
    _subscription = _channel!.stream.listen((raw) {
      try {
        final decoded = jsonDecode(raw.toString());
        if (decoded is Map<String, dynamic>) onEvent(decoded);
      } catch (_) {}
    });
  }

  Future<void> close() async {
    await _subscription?.cancel();
    _subscription = null;
    await _channel?.sink.close();
    _channel = null;
  }
}
