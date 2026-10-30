import '../../domain/repositories/admin_repository.dart';
import '../datasources/admin_remote_data_source.dart';

class AdminRepositoryImpl implements AdminRepository {
  const AdminRepositoryImpl(this._remote);

  final AdminRemoteDataSource _remote;

  @override
  Future<Map<String, dynamic>> getDashboard() => _remote.dashboard();

  @override
  Future<Map<String, dynamic>> getUsers({
    String query = '',
    String? status,
    String? role,
    int limit = 30,
    int offset = 0,
  }) => _remote.users(
    query: query,
    status: status,
    role: role,
    limit: limit,
    offset: offset,
  );

  @override
  Future<Map<String, dynamic>> getUserRagUsage(
    String userId, {
    String period = '30d',
    int offset = 0,
  }) => _remote.userRagUsage(userId, period, offset);

  @override
  Future<void> updateUserStatus(
    String userId, {
    required String status,
    required String reason,
  }) => _remote.updateStatus(userId, status, reason);

  @override
  Future<void> disciplineUser(
    String userId, {
    required String action,
    required String reason,
    int? durationDays,
  }) => _remote.discipline(
    userId,
    action: action,
    reason: reason,
    durationDays: durationDays,
  );

  @override
  Future<void> setGroupAdmin(
    String userId, {
    required String groupId,
    required bool grant,
  }) => _remote.setGroupAdmin(userId, groupId: groupId, grant: grant);

  Future<List<Map<String, dynamic>>> _maps(
    Future<List<dynamic>> source,
  ) async => (await source)
      .map((item) => Map<String, dynamic>.from(item as Map))
      .toList();

  @override
  Future<List<Map<String, dynamic>>> getReports({String? status}) =>
      _maps(_remote.reports(status: status));

  @override
  Future<void> resolveReport(
    String reportId, {
    required String decision,
    required String action,
    required String note,
  }) => _remote.resolveReport(
    reportId,
    decision: decision,
    action: action,
    note: note,
  );

  @override
  Future<List<Map<String, dynamic>>> getAuditLogs() =>
      _maps(_remote.auditLogs());

  @override
  Future<Map<String, dynamic>> getMaintenance() => _remote.maintenance();

  @override
  Future<Map<String, dynamic>> updateMaintenance({
    required bool enabled,
    required String message,
  }) => _remote.updateMaintenance(enabled: enabled, message: message);

  @override
  Future<List<Map<String, dynamic>>> getKeywords() => _maps(_remote.keywords());

  @override
  Future<void> createKeyword({
    required String keyword,
    required String action,
  }) async {
    await _remote.createKeyword(keyword: keyword, action: action);
  }

  @override
  Future<void> updateKeyword(
    String id, {
    String? keyword,
    String? action,
    bool? isActive,
  }) async {
    await _remote.updateKeyword(id, {
      'keyword': ?keyword,
      'action': ?action,
      'is_active': ?isActive,
    });
  }

  @override
  Future<void> deleteKeyword(String id) => _remote.deleteKeyword(id);
}
