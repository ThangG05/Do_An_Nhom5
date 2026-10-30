import '../../../../core/api_client.dart';
import '../../domain/repositories/ai_repository.dart';

class AiRepositoryImpl implements AiRepository {
  const AiRepositoryImpl(this._api);

  final ApiClient _api;

  @override
  Future<Map<String, dynamic>> ask(String question, {String? conversationId}) =>
      _api.postAuthenticated('/ai/chat', {
        'question': question,
        'conversation_id': conversationId,
      });

  @override
  Future<List<Map<String, dynamic>>> getConversations() async =>
      (await _api.getList('/ai/conversations'))
          .map((value) => Map<String, dynamic>.from(value as Map))
          .toList();

  @override
  Future<List<Map<String, dynamic>>> getMessages(String conversationId) async {
    final response = await _api.getObject('/ai/conversations/$conversationId/messages');
    return ((response['messages'] as List?) ?? const [])
        .map((value) => Map<String, dynamic>.from(value as Map))
        .toList();
  }

  @override
  Future<Map<String, dynamic>> createConversation({String? title}) =>
      _api.postAuthenticated('/ai/conversations', {'title': title});

  @override
  Future<void> renameConversation(String conversationId, String title) async {
    await _api.patch('/ai/conversations/$conversationId', {'title': title});
  }

  @override
  Future<void> deleteConversation(String conversationId) =>
      _api.delete('/ai/conversations/$conversationId');
}
