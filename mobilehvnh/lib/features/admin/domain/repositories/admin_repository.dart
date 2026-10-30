abstract interface class AdminRepository {
  Future<Map<String, dynamic>> getDashboard();
  Future<Map<String, dynamic>> getUsers({
    String query,
    String? status,
    String? role,
    int limit,
    int offset,
  });
  Future<Map<String, dynamic>> getUserRagUsage(
    String userId, {
    String period = '30d',
    int offset = 0,
  });
  Future<void> updateUserStatus(
    String userId, {
    required String status,
    required String reason,
  });
  Future<void> disciplineUser(
    String userId, {
    required String action,
    required String reason,
    int? durationDays,
  });
  Future<void> setGroupAdmin(
    String userId, {
    required String groupId,
    required bool grant,
  });
  Future<List<Map<String, dynamic>>> getReports({String? status});
  Future<void> resolveReport(
    String reportId, {
    required String decision,
    required String action,
    required String note,
  });
  Future<List<Map<String, dynamic>>> getAuditLogs();
  Future<Map<String, dynamic>> getMaintenance();
  Future<Map<String, dynamic>> updateMaintenance({
    required bool enabled,
    required String message,
  });
  Future<List<Map<String, dynamic>>> getKeywords();
  Future<void> createKeyword({required String keyword, required String action});
  Future<void> updateKeyword(
    String id, {
    String? keyword,
    String? action,
    bool? isActive,
  });
  Future<void> deleteKeyword(String id);
}
