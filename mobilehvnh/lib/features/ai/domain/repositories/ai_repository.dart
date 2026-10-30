abstract interface class AiRepository {
  Future<Map<String, dynamic>> ask(String question, {String? conversationId});
  Future<List<Map<String, dynamic>>> getConversations();
  Future<List<Map<String, dynamic>>> getMessages(String conversationId);
  Future<Map<String, dynamic>> createConversation({String? title});
  Future<void> renameConversation(String conversationId, String title);
  Future<void> deleteConversation(String conversationId);
}
