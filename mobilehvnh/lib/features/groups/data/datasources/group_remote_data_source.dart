import '../../../../core/api_client.dart';
import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';

class GroupRemoteDataSource {
  const GroupRemoteDataSource(this._api);

  final ApiClient _api;

  Future<List<dynamic>> groups() => _api.getList('/groups');
  Future<List<dynamic>> posts(
    String id, {
    String query = '',
    String sort = 'latest',
    bool mine = false,
    int limit = 10,
    int offset = 0,
  }) {
    final params = <String>[
      'limit=$limit',
      'offset=$offset',
    ];
    if (mine) {
      return _api.getList('/groups/$id/posts/mine?${params.join('&')}');
    }
    params.addAll([
      if (query.trim().isNotEmpty)
        'q=${Uri.encodeQueryComponent(query.trim())}',
      'sort=${Uri.encodeQueryComponent(sort)}',
    ]);
    return _api.getList('/groups/$id/posts?${params.join('&')}');
  }

  Future<void> join(String id) async =>
      _api.postAuthenticated('/groups/$id/join', {});
  Future<void> leave(String id) => _api.delete('/groups/$id/leave');
  Future<void> create(String id, Map<String, dynamic> body) async =>
      _api.postAuthenticated('/groups/$id/posts', body);
  Future<List<dynamic>> pendingPosts(String id) =>
      _api.getList('/groups/$id/admin/posts/pending');
  Future<List<dynamic>> members(String id) =>
      _api.getList('/groups/$id/admin/members');
  Future<List<dynamic>> joinRequests(String id) =>
      _api.getList('/groups/$id/admin/join-requests');
  Future<void> moderate(
    String groupId,
    String postId,
    Map<String, dynamic> body,
  ) async => _api.patch('/groups/$groupId/admin/posts/$postId/moderate', body);
  Future<void> decideRequest(
    String groupId,
    String requestId,
    Map<String, dynamic> body,
  ) async =>
      _api.patch('/groups/$groupId/admin/join-requests/$requestId', body);
  Future<void> removeMember(String groupId, String userId) =>
      _api.delete('/groups/$groupId/admin/members/$userId');
  Future<void> pinPost(String groupId, String postId, bool pinned) async => _api
      .put('/groups/$groupId/admin/posts/$postId/pin', {'is_pinned': pinned});
  Future<void> removePost(String groupId, String postId, String reason) =>
      _api.deleteWithBody('/groups/$groupId/admin/posts/$postId', {
        'reason': reason,
      });
  Future<String> upload(dynamic file) => _api.uploadPostFile(file);
  Future<List<dynamic>> studyMajors() => _api.getList('/majors');
  Future<List<dynamic>> studySubjects(
    String query, {
    String? majorId,
  }) => _api.getList(
    '/subjects?q=${Uri.encodeQueryComponent(query)}&limit=50${majorId == null ? '' : '&major_id=${Uri.encodeQueryComponent(majorId)}'}',
  );
  Future<List<dynamic>> studyDocuments(
    String id, {
    String query = '',
    String? subjectId,
    String? documentType,
    String? assessmentType,
    int offset = 0,
    bool mine = false,
    bool pending = false,
  }) {
    final base = pending
        ? '/groups/$id/library/admin/pending'
        : mine
        ? '/groups/$id/library/mine'
        : '/groups/$id/library';
    return _api.getList(
      '$base?limit=${mine || pending ? 5 : 6}&offset=$offset${query.isNotEmpty && !mine && !pending ? '&q=${Uri.encodeQueryComponent(query)}' : ''}'
      '${subjectId == null || mine || pending ? '' : '&subject_id=$subjectId'}'
      '${documentType == null || mine || pending ? '' : '&document_type=$documentType'}'
      '${assessmentType == null || mine || pending ? '' : '&assessment_type=$assessmentType'}',
    );
  }

  Future<List<dynamic>> studyAIAssessments(
    String id,
    List<String> documentIds,
  ) => _api.getList(
    '/groups/$id/library/admin/ai-assessments?${documentIds.map((value) => 'document_ids=${Uri.encodeQueryComponent(value)}').join('&')}',
  );

  Future<Map<String, dynamic>> shareStudyDocument(
    String id,
    String majorId,
    String subjectId,
    String documentType,
    String? assessmentType,
    String title,
    String description,
    List<PlatformFile> files,
  ) => _api.postFiles('/groups/$id/library', {
    'major_id': majorId,
    'subject_id': subjectId,
    'document_type': documentType,
    if (assessmentType != null) 'assessment_type': assessmentType,
    'title': title,
    'description': description,
  }, files);
  Future<Map<String, dynamic>> studyFileLink(
    String id,
    String documentId,
    String fileId,
    bool preview,
  ) => _api.getObject(
    '/groups/$id/library/$documentId/files/$fileId/download?preview=$preview',
  );
  Future<Map<String, dynamic>> studyOfficePreview(
    String id,
    String documentId,
    String fileId,
  ) => _api.getObject(
    '/groups/$id/library/$documentId/files/$fileId/preview-office',
  );
  Future<Uint8List> studyBundle(String id, String documentId) =>
      _api.downloadBytes('/groups/$id/library/$documentId/download-bundle');
  Future<void> deleteStudyDocument(String id, String documentId) =>
      _api.delete('/groups/$id/library/$documentId');
  Future<void> reportStudyDocument(
    String id,
    String documentId,
    String reason,
  ) async => _api.postAuthenticated('/groups/$id/library/$documentId/reports', {
    'reason': reason,
  });
  Future<void> moderateStudyDocument(
    String id,
    String documentId,
    bool approved,
    String reason,
  ) async => _api.patch('/groups/$id/library/admin/$documentId', {
    'decision': approved ? 'APPROVE' : 'REJECT',
    'reason': reason,
  });
  Future<List<dynamic>> studyDocumentReports(String id) =>
      _api.getList('/groups/$id/library/admin/reports?limit=50');
  Future<void> decideStudyDocumentReport(
    String id,
    String reportId,
    bool remove,
    String note,
  ) async => _api.patch('/groups/$id/library/admin/reports/$reportId', {
    'decision': remove ? 'REMOVE_DOCUMENT' : 'DISMISS',
    'note': note,
  });
  Future<List<dynamic>> adminStudySubjects(
    String id,
    String query,
    int offset,
  ) => _api.getList(
    '/groups/$id/library/admin/subjects?q=${Uri.encodeQueryComponent(query)}&limit=10&offset=$offset',
  );
  Future<void> saveStudySubject(
    String id,
    Map<String, dynamic> payload,
  ) async => _api.put('/groups/$id/library/admin/subjects', payload);
  Future<List<dynamic>> groupReports() =>
      _api.getList('/reports/admin?status=OPEN');
  Future<void> resolveGroupReport(
    String reportId,
    bool hideContent,
    String note, {
    bool alreadyRemoved = false,
  }) async => _api.patch('/reports/admin/$reportId', {
    'decision': alreadyRemoved || hideContent ? 'RESOLVE' : 'REJECT',
    'action': alreadyRemoved
        ? 'NONE'
        : hideContent
        ? 'HIDE_CONTENT'
        : 'NONE',
    'note': note,
  });
}
