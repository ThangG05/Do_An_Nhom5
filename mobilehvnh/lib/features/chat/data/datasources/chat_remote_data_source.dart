import '../../../../core/api_client.dart';

class ChatRemoteDataSource {
  const ChatRemoteDataSource(this._api);

  final ApiClient _api;

  Future<List<dynamic>> conversations() => _api.getList('/chat/conversations');

  Future<List<dynamic>> messages(String id, {String? before, int limit = 50}) {
    final query = <String>[
      'limit=$limit',
      if (before != null && before.isNotEmpty)
        'before=${Uri.encodeQueryComponent(before)}',
    ];
    return _api.getList('/chat/conversations/$id/messages?${query.join('&')}');
  }

  Future<Map<String, dynamic>> send(String id, Map<String, dynamic> body) =>
      _api.postAuthenticated('/chat/conversations/$id/messages', body);

  Future<Map<String, dynamic>> recall(String id, String messageId) =>
      _api.deleteObject('/chat/conversations/$id/messages/$messageId');

  Future<Map<String, dynamic>> createDirectConversation(String userId) =>
      _api.postAuthenticated('/chat/conversations/direct', {
        'target_user_id': userId,
      });

  Future<void> updateSettings(String id, Map<String, dynamic> body) async {
    await _api.patch('/chat/conversations/$id/settings', body);
  }

  Future<Map<String, dynamic>> sharedAttachments(String id) =>
      _api.getObject('/chat/conversations/$id/shared');

  Future<List<dynamic>> searchMessages(String id, String query) => _api.getList(
    '/chat/conversations/$id/messages/search?q=${Uri.encodeQueryComponent(query)}',
  );

  Future<String> upload(dynamic file) =>
      _api.uploadFile(file, endpoint: '/media/upload/message');
}
