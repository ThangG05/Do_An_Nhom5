abstract interface class NotificationRepository {
  Future<Map<String, dynamic>> getPage({
    String filter = 'all',
    int offset = 0,
    int limit = 30,
  });
  Future<void> readAll();
  Future<void> setRead(String id, bool isRead);
  Future<void> delete(String id);
}
