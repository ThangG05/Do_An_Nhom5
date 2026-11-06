import 'dart:async';
import 'dart:convert';

import 'package:web_socket_channel/web_socket_channel.dart';

import 'api_client.dart';
import 'app_config.dart';

class ChatRealtime {
  ChatRealtime(this._api);

  final ApiClient _api;
  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _subscription;
  Timer? _retryTimer;
  Timer? _heartbeatTimer;
  void Function(Map<String, dynamic>)? _onEvent;
  void Function()? _onConnected;
  bool _disposed = true;
  bool _connecting = false;
  int _retryAttempt = 0;
  DateTime _lastPongAt = DateTime.fromMillisecondsSinceEpoch(0);

  Future<void> connect(
    void Function(Map<String, dynamic> event) onEvent, {
    void Function()? onConnected,
  }) async {
    await close();
    _disposed = false;
    _retryAttempt = 0;
    _onEvent = onEvent;
    _onConnected = onConnected;
    await _open();
  }

  /// Replaces a possibly stale connection, for example when Android resumes.
  Future<void> reconnect() async {
    if (_disposed) return;
    _retryTimer?.cancel();
    _retryTimer = null;
    await _clearChannel();
    await _open();
  }

  Future<void> _open() async {
    if (_disposed || _connecting) return;
    _connecting = true;
    try {
      final ticket = await _api.postAuthenticated('/chat/ws-ticket', {});
      final value = ticket['ticket']?.toString();
      if (_disposed) return;
      if (value == null || value.isEmpty) {
        _scheduleReconnect();
        return;
      }

      final base = AppConfig.apiBaseUrl.replaceFirst(RegExp(r'^http'), 'ws');
      final channel = WebSocketChannel.connect(
        Uri.parse('$base/chat/ws?ticket=${Uri.encodeQueryComponent(value)}'),
      );
      _channel = channel;
      await channel.ready.timeout(const Duration(seconds: 15));
      if (_disposed) {
        await channel.sink.close();
        return;
      }
      if (!identical(_channel, channel)) {
        await channel.sink.close();
        _scheduleReconnect();
        return;
      }

      _retryAttempt = 0;
      _lastPongAt = DateTime.now();
      _subscription = channel.stream.listen(
        _handleFrame,
        onError: (Object _) => _scheduleReconnect(channel),
        onDone: () => _scheduleReconnect(channel),
        cancelOnError: true,
      );
      _heartbeatTimer?.cancel();
      _heartbeatTimer = Timer.periodic(const Duration(seconds: 25), (_) {
        if (_disposed || !identical(_channel, channel)) return;
        if (DateTime.now().difference(_lastPongAt) >
            const Duration(seconds: 55)) {
          _scheduleReconnect(channel);
          return;
        }
        try {
          channel.sink.add('ping');
        } catch (_) {
          _scheduleReconnect(channel);
        }
      });
      _onConnected?.call();
    } catch (_) {
      _scheduleReconnect();
    } finally {
      _connecting = false;
    }
  }

  void _handleFrame(dynamic raw) {
    if (raw.toString() == 'pong') {
      _lastPongAt = DateTime.now();
      return;
    }
    try {
      final decoded = jsonDecode(raw.toString());
      if (decoded is Map<String, dynamic>) _onEvent?.call(decoded);
    } catch (_) {
      // Ignore malformed frames without interrupting the connection.
    }
  }

  void _scheduleReconnect([WebSocketChannel? expectedChannel]) {
    if (_disposed || _retryTimer != null) return;
    if (expectedChannel != null && !identical(_channel, expectedChannel)) {
      return;
    }

    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    unawaited(_clearChannel());

    const delays = [1, 2, 4, 8, 15, 30];
    final seconds = delays[_retryAttempt.clamp(0, delays.length - 1).toInt()];
    _retryAttempt += 1;
    _retryTimer = Timer(Duration(seconds: seconds), () {
      _retryTimer = null;
      unawaited(_open());
    });
  }

  Future<void> _clearChannel() async {
    _heartbeatTimer?.cancel();
    _heartbeatTimer = null;
    final subscription = _subscription;
    _subscription = null;
    await subscription?.cancel();
    final channel = _channel;
    _channel = null;
    if (channel != null) {
      try {
        await channel.sink.close();
      } catch (_) {
        // The socket may already have been closed by the network stack.
      }
    }
  }

  Future<void> close() async {
    _disposed = true;
    _retryTimer?.cancel();
    _retryTimer = null;
    _onEvent = null;
    _onConnected = null;
    await _clearChannel();
  }
}
