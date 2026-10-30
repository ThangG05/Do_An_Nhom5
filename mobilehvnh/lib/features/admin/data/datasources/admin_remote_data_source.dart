import '../../../../core/api_client.dart';

class AdminRemoteDataSource {
  const AdminRemoteDataSource(this._api);

  final ApiClient _api;

  Future<Map<String, dynamic>> dashboard() =>
      _api.getObject('/admin/dashboard');

  Future<Map<String, dynamic>> users({
    String query = '',
    String? status,
    String? role,
    int limit = 30,
    int offset = 0,
  }) {
    final params = <String>[
      'limit=$limit',
      'offset=$offset',
      if (query.trim().isNotEmpty)
        'q=${Uri.encodeQueryComponent(query.trim())}',
      if (status != null) 'status=${Uri.encodeQueryComponent(status)}',
      if (role != null) 'role=${Uri.encodeQueryComponent(role)}',
    ];
    return _api.getObject('/admin/users?${params.join('&')}');
  }

  Future<Map<String, dynamic>> userRagUsage(
    String id,
    String period,
    int offset,
  ) => _api.getObject(
    '/admin/users/$id/rag-usage?period=$period&offset=$offset',
  );

  Future<void> updateStatus(String userId, String status, String reason) async {
    await _api.patch('/admin/users/$userId/status', {
      'status': status,
      'reason': reason,
    });
  }

  Future<void> discipline(
    String userId, {
    required String action,
    required String reason,
    int? durationDays,
  }) async {
    await _api.postAuthenticated('/admin/users/$userId/discipline', {
      'action': action,
      'reason': reason,
      'duration_days': ?durationDays,
    });
  }

  Future<void> setGroupAdmin(
    String userId, {
    required String groupId,
    required bool grant,
  }) async {
    await _api.put('/admin/users/$userId/group-admin', {
      'group_id': groupId,
      'grant': grant,
    });
  }

  Future<List<dynamic>> reports({String? status}) => _api.getList(
    '/reports/admin${status == null ? '' : '?status=${Uri.encodeQueryComponent(status)}'}',
  );

  Future<void> resolveReport(
    String reportId, {
    required String decision,
    required String action,
    required String note,
  }) async {
    await _api.patch('/reports/admin/$reportId', {
      'decision': decision,
      'action': action,
      'note': note,
    });
  }

  Future<List<dynamic>> auditLogs() =>
      _api.getList('/admin/audit-logs?limit=100');

  Future<Map<String, dynamic>> maintenance() =>
      _api.getObject('/system/status');

  Future<Map<String, dynamic>> updateMaintenance({
    required bool enabled,
    required String message,
  }) => _api.put('/system/admin/maintenance', {
    'enabled': enabled,
    'message': message,
  });

  Future<List<dynamic>> keywords() => _api.getList('/system/admin/keywords');

  Future<Map<String, dynamic>> createKeyword({
    required String keyword,
    required String action,
  }) => _api.postAuthenticated('/system/admin/keywords', {
    'keyword': keyword,
    'action': action,
  });

  Future<Map<String, dynamic>> updateKeyword(
    String id,
    Map<String, dynamic> body,
  ) => _api.patch('/system/admin/keywords/$id', body);

  Future<void> deleteKeyword(String id) =>
      _api.delete('/system/admin/keywords/$id');
}
