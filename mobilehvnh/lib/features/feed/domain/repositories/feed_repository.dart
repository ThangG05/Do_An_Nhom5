import '../entities/upload_file.dart';

abstract interface class FeedRepository {
  Future<List<Map<String, dynamic>>> getFeed({String? category});
  Future<({List<Map<String, dynamic>> items, String? nextCursor})> getFeedPage({
    String? category,
    String? cursor,
    int limit,
  });
  Future<void> createPost({
    required String content,
    required List<UploadFile> files,
    String category,
    Map<String, dynamic>? marketListing,
    Map<String, dynamic>? roomListing,
    Map<String, dynamic>? eventListing,
    Map<String, dynamic>? studyListing,
    Map<String, dynamic>? location,
  });
  Future<Map<String, dynamic>> setLike(String postId, bool isLiked);
  Future<Map<String, dynamic>> getPostLikes(
    String postId, {
    int limit = 50,
    int offset = 0,
  });
  Future<List<Map<String, dynamic>>> getComments(String postId);
  Future<void> addComment(
    String postId,
    String content, {
    String? parentId,
    UploadFile? image,
    List<Map<String, dynamic>> mentions = const [],
  });
  Future<List<Map<String, dynamic>>> getMentionableFriends(String userId);
  Future<Map<String, dynamic>> updatePost(
    String postId, {
    required String content,
    String? privacy,
    String? category,
    List<String>? mediaIds,
  });
  Future<void> deletePost(String postId);
  Future<void> reportPost(String postId, String reason);
  Future<Map<String, dynamic>> updateComment(
    String commentId, {
    required String content,
  });
  Future<void> deleteComment(String commentId);
  Future<Map<String, dynamic>> getPost(String postId);
  Future<List<Map<String, dynamic>>> searchLocations(String query);
  Future<Map<String, dynamic>?> reverseLocation(
    double latitude,
    double longitude,
  );
}
