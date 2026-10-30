import '../../../../core/api_client.dart';

class FeedRemoteDataSource {
  const FeedRemoteDataSource(this._apiClient);
  final ApiClient _apiClient;
  Future<List<dynamic>> feed({String? category}) => _apiClient.getList(
    '/posts/feed?limit=30${category == null ? '' : '&category=${Uri.encodeQueryComponent(category)}'}',
  );
  Future<({List<dynamic> items, String? nextCursor})> feedPage({
    String? category,
    String? cursor,
    int limit = 20,
  }) {
    final params = <String>[
      'limit=$limit',
      if (cursor != null && cursor.isNotEmpty)
        'cursor=${Uri.encodeQueryComponent(cursor)}',
      if (category != null && category.isNotEmpty)
        'category=${Uri.encodeQueryComponent(category)}',
    ];
    return _apiClient.getListPage('/posts/feed?${params.join('&')}');
  }

  Future<Map<String, dynamic>> create(Map<String, dynamic> body) =>
      _apiClient.post('/users/me/posts', body, authenticated: true);
  Future<Map<String, dynamic>> like(String id, bool isLiked) =>
      _apiClient.put('/posts/$id/like', {'is_liked': isLiked});
  Future<Map<String, dynamic>> likes(
    String id, {
    int limit = 50,
    int offset = 0,
  }) => _apiClient.getObject('/posts/$id/likes?limit=$limit&offset=$offset');
  Future<List<dynamic>> comments(String id) =>
      _apiClient.getList('/posts/$id/comments');
  Future<Map<String, dynamic>> comment(
    String id, {
    required String content,
    String? parentId,
    String? mediaId,
    List<Map<String, dynamic>> mentions = const [],
  }) => _apiClient.postAuthenticated('/posts/$id/comments', {
    'content': content,
    'parent_id': ?parentId,
    'media_id': ?mediaId,
    'mentions': mentions,
  });
  Future<List<dynamic>> friends(String userId) =>
      _apiClient.getList('/users/$userId/friends');
  Future<Map<String, dynamic>> updatePost(
    String id, {
    required String content,
    String? privacy,
    String? category,
    List<String>? mediaIds,
  }) => _apiClient.patch('/posts/$id', {
    'content': content,
    'privacy': ?privacy,
    'category': ?category,
    'media_ids': ?mediaIds,
  });
  Future<void> deletePost(String id) => _apiClient.delete('/posts/$id');
  Future<void> reportPost(String id, String reason) async =>
      _apiClient.postAuthenticated('/reports', {
        'target_type': 'POST',
        'target_id': id,
        'reason': reason,
      });
  Future<Map<String, dynamic>> updateComment(String id, String content) =>
      _apiClient.patch('/posts/comments/$id', {'content': content});
  Future<void> deleteComment(String id) =>
      _apiClient.delete('/posts/comments/$id');
  Future<Map<String, dynamic>> post(String id) =>
      _apiClient.getObject('/posts/$id');
  Future<List<dynamic>> searchLocations(String query) => _apiClient.getList(
    '/locations/search?q=${Uri.encodeQueryComponent(query)}&limit=5',
  );
  Future<Map<String, dynamic>?> reverseLocation(
    double latitude,
    double longitude,
  ) => _apiClient.getOptionalObject(
    '/locations/reverse?latitude=$latitude&longitude=$longitude',
  );
  Future<String> upload(dynamic file) => _apiClient.uploadPostFile(file);
  Future<String> uploadComment(dynamic file) =>
      _apiClient.uploadFile(file, endpoint: '/media/upload/comment');
}
