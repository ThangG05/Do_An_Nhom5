import '../../domain/repositories/notification_repository.dart';
import '../datasources/notification_remote_data_source.dart';

class NotificationRepositoryImpl implements NotificationRepository {
  const NotificationRepositoryImpl(this._remote);
  final NotificationRemoteDataSource _remote;
  @override
  Future<Map<String, dynamic>> getPage({
    String filter = 'all',
    int offset = 0,
    int limit = 30,
  }) => _remote.page(filter: filter, offset: offset, limit: limit);
  @override
  Future<void> readAll() => _remote.readAll();
  @override
  Future<void> setRead(String id, bool value) => _remote.setRead(id, value);
  @override
  Future<void> delete(String id) => _remote.delete(id);
}
