import '../../../../core/api_client.dart';

class NotificationRemoteDataSource {
  const NotificationRemoteDataSource(this._api);
  final ApiClient _api;
  Future<Map<String, dynamic>> page({
    String filter = 'all',
    int offset = 0,
    int limit = 30,
  }) => _api.getObject(
    '/notifications?limit=$limit&offset=$offset&unread_only=${filter == 'unread'}&friend_only=${filter == 'friends'}',
  );
  Future<void> readAll() async {
    await _api.postAuthenticated('/notifications/read-all', {});
  }

  Future<void> setRead(String id, bool value) async {
    await _api.patch('/notifications/$id', {'is_read': value});
  }

  Future<void> delete(String id) => _api.delete('/notifications/$id');
}
