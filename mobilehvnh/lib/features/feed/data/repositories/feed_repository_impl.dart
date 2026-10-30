import 'package:file_picker/file_picker.dart';
import '../../domain/entities/upload_file.dart';
import '../../domain/repositories/feed_repository.dart';
import '../datasources/feed_remote_data_source.dart';

class FeedRepositoryImpl implements FeedRepository {
  const FeedRepositoryImpl(this._remote);
  final FeedRemoteDataSource _remote;
  @override
  Future<List<Map<String, dynamic>>> getFeed({String? category}) async =>
      (await _remote.feed(
        category: category,
      )).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  @override
  Future<({List<Map<String, dynamic>> items, String? nextCursor})> getFeedPage({
    String? category,
    String? cursor,
    int limit = 20,
  }) async {
    final page = await _remote.feedPage(
      category: category,
      cursor: cursor,
      limit: limit,
    );
    return (
      items: page.items
          .map((item) => Map<String, dynamic>.from(item as Map))
          .toList(),
      nextCursor: page.nextCursor,
    );
  }

  @override
  Future<void> createPost({
    required String content,
    required List<UploadFile> files,
    String category = 'general',
    Map<String, dynamic>? marketListing,
    Map<String, dynamic>? roomListing,
    Map<String, dynamic>? eventListing,
    Map<String, dynamic>? studyListing,
    Map<String, dynamic>? location,
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
    await _remote.create({
      'content': content,
      'form_version': 2,
      'privacy': 'public',
      'category': category,
      'media_ids': ids,
      'marketListing': ?marketListing,
      'roomListing': ?roomListing,
      'eventListing': ?eventListing,
      'studyListing': ?studyListing,
      'location': ?location,
    });
  }

  @override
  Future<Map<String, dynamic>> setLike(String id, bool liked) =>
      _remote.like(id, liked);
  @override
  Future<Map<String, dynamic>> getPostLikes(
    String id, {
    int limit = 50,
    int offset = 0,
  }) => _remote.likes(id, limit: limit, offset: offset);
  @override
  Future<List<Map<String, dynamic>>> getComments(String id) async =>
      (await _remote.comments(
        id,
      )).map((e) => Map<String, dynamic>.from(e as Map)).toList();
  @override
  Future<void> addComment(
    String id,
    String content, {
    String? parentId,
    UploadFile? image,
    List<Map<String, dynamic>> mentions = const [],
  }) async {
    String? mediaId;
    if (image != null) {
      mediaId = await _remote.uploadComment(
        PlatformFile(
          name: image.name,
          size: image.size,
          path: image.path,
          bytes: image.bytes,
        ),
      );
    }
    await _remote.comment(
      id,
      content: content,
      parentId: parentId,
      mediaId: mediaId,
      mentions: mentions,
    );
  }

  @override
  Future<List<Map<String, dynamic>>> getMentionableFriends(
    String userId,
  ) async => (await _remote.friends(
    userId,
  )).map((item) => Map<String, dynamic>.from(item as Map)).toList();

  @override
  Future<Map<String, dynamic>> updatePost(
    String id, {
    required String content,
    String? privacy,
    String? category,
    List<String>? mediaIds,
  }) => _remote.updatePost(
    id,
    content: content,
    privacy: privacy,
    category: category,
    mediaIds: mediaIds,
  );
  @override
  Future<void> deletePost(String id) => _remote.deletePost(id);
  @override
  Future<void> reportPost(String id, String reason) =>
      _remote.reportPost(id, reason);
  @override
  Future<Map<String, dynamic>> updateComment(
    String id, {
    required String content,
  }) => _remote.updateComment(id, content);
  @override
  Future<void> deleteComment(String id) => _remote.deleteComment(id);
  @override
  Future<Map<String, dynamic>> getPost(String id) => _remote.post(id);
  @override
  Future<List<Map<String, dynamic>>> searchLocations(String query) async =>
      (await _remote.searchLocations(
        query,
      )).map((item) => Map<String, dynamic>.from(item as Map)).toList();
  @override
  Future<Map<String, dynamic>?> reverseLocation(
    double latitude,
    double longitude,
  ) async {
    final value = await _remote.reverseLocation(latitude, longitude);
    return value == null || value.isEmpty ? null : value;
  }
}
