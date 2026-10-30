import 'package:file_picker/file_picker.dart';
import 'dart:typed_data';

import '../../domain/entities/group_upload_file.dart';
import '../../domain/repositories/group_repository.dart';
import '../datasources/group_remote_data_source.dart';

class GroupRepositoryImpl implements GroupRepository {
  const GroupRepositoryImpl(this._remote);
  final GroupRemoteDataSource _remote;

  Future<List<Map<String, dynamic>>> _maps(
    Future<List<dynamic>> source,
  ) async => (await source)
      .map((value) => Map<String, dynamic>.from(value as Map))
      .toList();

  @override
  Future<List<Map<String, dynamic>>> getGroups() => _maps(_remote.groups());

  @override
  Future<List<Map<String, dynamic>>> getPosts(
    String id, {
    String query = '',
    String sort = 'latest',
    bool mine = false,
    int limit = 10,
    int offset = 0,
  }) async {
    final posts = await _maps(
      _remote.posts(
        id,
        query: query,
        sort: sort,
        mine: mine,
        limit: limit,
        offset: offset,
      ),
    );
    if (!mine || query.trim().isEmpty) return posts;
    final normalized = query.trim().toLowerCase();
    return posts
        .where(
          (post) =>
              '${post['content'] ?? ''}'.toLowerCase().contains(normalized),
        )
        .toList();
  }

  @override
  Future<void> requestJoin(String id) => _remote.join(id);

  @override
  Future<void> leaveGroup(String id) => _remote.leave(id);

  @override
  Future<void> createPost(
    String id,
    String content,
    List<GroupUploadFile> files, {
    Map<String, dynamic>? marketListing,
    Map<String, dynamic>? roomListing,
    Map<String, dynamic>? eventListing,
    Map<String, dynamic>? studyListing,
    Map<String, dynamic>? location,
  }) async {
    final mediaIds = <String>[];
    for (final file in files) {
      mediaIds.add(
        await _remote.upload(
          PlatformFile(
            name: file.name,
            size: file.size,
            path: file.path,
            bytes: file.bytes,
          ),
        ),
      );
    }
    await _remote.create(id, {
      'form_version': 2,
      'content': content,
      'media_ids': mediaIds,
      'marketListing': ?marketListing,
      'roomListing': ?roomListing,
      'eventListing': ?eventListing,
      'studyListing': ?studyListing,
      'location': ?location,
    });
  }

  @override
  Future<List<Map<String, dynamic>>> getPendingPosts(String id) =>
      _maps(_remote.pendingPosts(id));

  @override
  Future<List<Map<String, dynamic>>> getMembers(String id) =>
      _maps(_remote.members(id));

  @override
  Future<List<Map<String, dynamic>>> getJoinRequests(String id) =>
      _maps(_remote.joinRequests(id));

  @override
  Future<void> moderatePost(
    String groupId,
    String postId, {
    required bool approved,
    String? reason,
  }) => _remote.moderate(groupId, postId, {
    'decision': approved ? 'APPROVE' : 'REJECT',
    'reason': reason,
  });

  @override
  Future<void> decideJoinRequest(
    String groupId,
    String requestId, {
    required bool approved,
  }) => _remote.decideRequest(groupId, requestId, {
    'decision': approved ? 'APPROVE' : 'REJECT',
  });

  @override
  Future<void> removeMember(String groupId, String userId) =>
      _remote.removeMember(groupId, userId);

  @override
  Future<void> pinPost(String groupId, String postId, {required bool pinned}) =>
      _remote.pinPost(groupId, postId, pinned);

  @override
  Future<void> removePost(
    String groupId,
    String postId, {
    required String reason,
  }) => _remote.removePost(groupId, postId, reason);

  @override
  Future<List<Map<String, dynamic>>> getStudyMajors() =>
      _maps(_remote.studyMajors());
  @override
  Future<List<Map<String, dynamic>>> getStudySubjects(
    String query, {
    String? majorId,
  }) => _maps(_remote.studySubjects(query, majorId: majorId));
  @override
  Future<List<Map<String, dynamic>>> getStudyDocuments(
    String groupId, {
    String query = '',
    String? subjectId,
    String? documentType,
    String? assessmentType,
    int offset = 0,
    bool mine = false,
    bool pending = false,
  }) => _maps(
    _remote.studyDocuments(
      groupId,
      query: query,
      subjectId: subjectId,
      documentType: documentType,
      assessmentType: assessmentType,
      offset: offset,
      mine: mine,
      pending: pending,
    ),
  );
  @override
  Future<List<Map<String, dynamic>>> getStudyAIAssessments(
    String groupId,
    List<String> documentIds,
  ) => _maps(_remote.studyAIAssessments(groupId, documentIds));
  @override
  Future<void> shareStudyDocument(
    String groupId,
    String majorId,
    String subjectId,
    String documentType,
    String? assessmentType,
    String title,
    String description,
    List<GroupUploadFile> files,
  ) async {
    await _remote.shareStudyDocument(
      groupId,
      majorId,
      subjectId,
      documentType,
      assessmentType,
      title,
      description,
      files
          .map(
            (file) => PlatformFile(
              name: file.name,
              size: file.size,
              path: file.path,
              bytes: file.bytes,
            ),
          )
          .toList(),
    );
  }

  @override
  Future<Map<String, dynamic>> getStudyFileLink(
    String groupId,
    String documentId,
    String fileId, {
    bool preview = false,
  }) => _remote.studyFileLink(groupId, documentId, fileId, preview);
  @override
  Future<Map<String, dynamic>> getStudyOfficePreview(
    String groupId,
    String documentId,
    String fileId,
  ) => _remote.studyOfficePreview(groupId, documentId, fileId);
  @override
  Future<Uint8List> downloadStudyBundle(String groupId, String documentId) =>
      _remote.studyBundle(groupId, documentId);
  @override
  Future<void> deleteStudyDocument(String groupId, String documentId) =>
      _remote.deleteStudyDocument(groupId, documentId);
  @override
  Future<void> reportStudyDocument(
    String groupId,
    String documentId,
    String reason,
  ) => _remote.reportStudyDocument(groupId, documentId, reason);
  @override
  Future<void> moderateStudyDocument(
    String groupId,
    String documentId,
    bool approved,
    String reason,
  ) => _remote.moderateStudyDocument(groupId, documentId, approved, reason);
  @override
  Future<List<Map<String, dynamic>>> getStudyDocumentReports(String groupId) =>
      _maps(_remote.studyDocumentReports(groupId));
  @override
  Future<void> decideStudyDocumentReport(
    String groupId,
    String reportId,
    bool remove,
    String note,
  ) => _remote.decideStudyDocumentReport(groupId, reportId, remove, note);
  @override
  Future<List<Map<String, dynamic>>> getAdminStudySubjects(
    String groupId,
    String query,
    int offset,
  ) => _maps(_remote.adminStudySubjects(groupId, query, offset));
  @override
  Future<void> saveStudySubject(String groupId, Map<String, dynamic> payload) =>
      _remote.saveStudySubject(groupId, payload);
  @override
  Future<List<Map<String, dynamic>>> getGroupReports(String groupId) async =>
      (await _maps(
        _remote.groupReports(),
      )).where((item) => item['group_id']?.toString() == groupId).toList();
  @override
  Future<void> resolveGroupReport(
    String reportId,
    bool hideContent,
    String note, {
    bool alreadyRemoved = false,
  }) => _remote.resolveGroupReport(
    reportId,
    hideContent,
    note,
    alreadyRemoved: alreadyRemoved,
  );
}
