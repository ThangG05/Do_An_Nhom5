import 'package:file_picker/file_picker.dart';

import '../../domain/entities/chat_upload_file.dart';
import '../../domain/repositories/chat_repository.dart';
import '../datasources/chat_remote_data_source.dart';

class ChatRepositoryImpl implements ChatRepository {
  const ChatRepositoryImpl(this._remote);

  final ChatRemoteDataSource _remote;

  @override
  Future<List<Map<String, dynamic>>> getConversations() async =>
      (await _remote.conversations())
          .map((value) => Map<String, dynamic>.from(value as Map))
          .toList();

  @override
  Future<List<Map<String, dynamic>>> getMessages(
    String id, {
    String? before,
    int limit = 50,
  }) async => (await _remote.messages(
    id,
    before: before,
    limit: limit,
  )).map((value) => Map<String, dynamic>.from(value as Map)).toList();

  @override
  Future<Map<String, dynamic>> sendMessage(
    String id,
    String content,
    List<ChatUploadFile> files, {
    String? replyToId,
  }) async {
    final ids = <String>[];
    for (final file in files) {
      ids.add(
        await _remote.upload(
          PlatformFile(
            name: file.name,
            size: file.size,
            path: file.path,
            bytes: file.bytes,
          ),
        ),
      );
    }
    return _remote.send(id, {
      'content': content,
      'media_ids': ids,
      'reply_to_id': ?replyToId,
    });
  }

  @override
  Future<Map<String, dynamic>> recallMessage(
    String conversationId,
    String messageId,
  ) => _remote.recall(conversationId, messageId);

  @override
  Future<Map<String, dynamic>> createDirectConversation(String userId) =>
      _remote.createDirectConversation(userId);

  @override
  Future<void> updateConversationSettings(
    String conversationId, {
    String? theme,
    String? nickname,
    bool? isMuted,
  }) => _remote.updateSettings(conversationId, {
    'theme': theme,
    'nickname': nickname,
    'is_muted': isMuted,
  });

  @override
  Future<Map<String, List<Map<String, dynamic>>>> getSharedAttachments(
    String conversationId,
  ) async {
    final response = await _remote.sharedAttachments(conversationId);
    List<Map<String, dynamic>> items(String key) =>
        ((response[key] as List?) ?? const [])
            .map((value) => Map<String, dynamic>.from(value as Map))
            .toList();
    return {'media': items('media'), 'files': items('files')};
  }

  @override
  Future<List<Map<String, dynamic>>> searchMessages(
    String conversationId,
    String query,
  ) async => (await _remote.searchMessages(
    conversationId,
    query,
  )).map((value) => Map<String, dynamic>.from(value as Map)).toList();
}
