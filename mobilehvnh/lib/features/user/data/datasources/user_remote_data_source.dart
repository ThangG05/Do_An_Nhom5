import 'package:file_picker/file_picker.dart';

import '../../../../core/api_client.dart';

class UserRemoteDataSource {
  const UserRemoteDataSource(this._api);
  final ApiClient _api;

  Future<Map<String, dynamic>> me() => _api.getObject('/users/me');
  Future<Map<String, dynamic>> profile(String id) => _api.getObject('/users/$id');
  Future<Map<String, dynamic>> update(Map<String, dynamic> value) => _api.patch('/users/me', value);
  Future<List<dynamic>> search(String query) => _api.getList('/users/search?q=${Uri.encodeQueryComponent(query)}');
  Future<List<dynamic>> friends(String id) => _api.getList('/users/$id/friends');
  Future<List<dynamic>> posts(String id) => _api.getList('/users/$id/posts');
  Future<List<dynamic>> photos(String id) => _api.getList('/users/$id/photos');
  Future<List<dynamic>> listings(String id, {String category = 'all'}) =>
      _api.getList('/users/$id/listings?category=${Uri.encodeQueryComponent(category)}');
  Future<List<dynamic>> groupPosts(String id) => _api.getList('/users/$id/group-posts');
  Future<List<dynamic>> blocked() => _api.getList('/users/me/blocked');

  Future<void> updateAvatar(PlatformFile file) async {
    final mediaId = await _api.uploadFile(file, endpoint: '/media/upload/avatar');
    await _api.put('/users/me/avatar', {'media_id': mediaId, 'create_post': false});
  }

  Future<void> updateCover(PlatformFile file) async {
    final mediaId = await _api.uploadFile(file, endpoint: '/media/upload/cover');
    await _api.put('/users/me/cover', {'media_id': mediaId});
  }

  Future<Map<String, dynamic>> friendship(String userId, String action) =>
      _api.postAuthenticated('/users/$userId/friendship', {'action': action});

  Future<void> setBlocked(String userId, bool blocked) =>
      blocked ? _api.put('/users/$userId/block', {}) : _api.delete('/users/$userId/block');

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _api.postAuthenticated('/auth/password/change', {
      'current_password': currentPassword,
      'new_password': newPassword,
    });
  }
}
