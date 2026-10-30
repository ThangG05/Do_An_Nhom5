import '../entities/chat_upload_file.dart';

abstract interface class ChatRepository {
  Future<List<Map<String, dynamic>>> getConversations();
  Future<List<Map<String, dynamic>>> getMessages(
    String conversationId, {
    String? before,
    int limit,
  });
  Future<Map<String, dynamic>> sendMessage(
    String conversationId,
    String content,
    List<ChatUploadFile> files, {
    String? replyToId,
  });
  Future<Map<String, dynamic>> recallMessage(
    String conversationId,
    String messageId,
  );
  Future<Map<String, dynamic>> createDirectConversation(String userId);
  Future<void> updateConversationSettings(
    String conversationId, {
    String? theme,
    String? nickname,
    bool? isMuted,
  });
  Future<Map<String, List<Map<String, dynamic>>>> getSharedAttachments(
    String conversationId,
  );
  Future<List<Map<String, dynamic>>> searchMessages(
    String conversationId,
    String query,
  );
}
