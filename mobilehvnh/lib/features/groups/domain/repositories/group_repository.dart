import '../entities/group_upload_file.dart';
import 'dart:typed_data';

abstract interface class GroupRepository {
  Future<List<Map<String, dynamic>>> getGroups();
  Future<List<Map<String, dynamic>>> getPosts(
    String groupId, {
    String query = '',
    String sort = 'latest',
    bool mine = false,
    int limit = 10,
    int offset = 0,
  });
  Future<void> requestJoin(String groupId);
  Future<void> leaveGroup(String groupId);
  Future<void> createPost(
    String groupId,
    String content,
    List<GroupUploadFile> files, {
    Map<String, dynamic>? marketListing,
    Map<String, dynamic>? roomListing,
    Map<String, dynamic>? eventListing,
    Map<String, dynamic>? studyListing,
    Map<String, dynamic>? location,
  });
  Future<List<Map<String, dynamic>>> getPendingPosts(String groupId);
  Future<List<Map<String, dynamic>>> getMembers(String groupId);
  Future<List<Map<String, dynamic>>> getJoinRequests(String groupId);
  Future<void> moderatePost(
    String groupId,
    String postId, {
    required bool approved,
    String? reason,
  });
  Future<void> decideJoinRequest(
    String groupId,
    String requestId, {
    required bool approved,
  });
  Future<void> removeMember(String groupId, String userId);
  Future<void> pinPost(String groupId, String postId, {required bool pinned});
  Future<void> removePost(
    String groupId,
    String postId, {
    required String reason,
  });
  Future<List<Map<String, dynamic>>> getStudyMajors();
  Future<List<Map<String, dynamic>>> getStudySubjects(
    String query, {
    String? majorId,
  });
  Future<List<Map<String, dynamic>>> getStudyDocuments(
    String groupId, {
    String query = '',
    String? subjectId,
    String? documentType,
    String? assessmentType,
    int offset = 0,
    bool mine = false,
    bool pending = false,
  });
  Future<List<Map<String, dynamic>>> getStudyAIAssessments(
    String groupId,
    List<String> documentIds,
  );
  Future<void> shareStudyDocument(
    String groupId,
    String majorId,
    String subjectId,
    String documentType,
    String? assessmentType,
    String title,
    String description,
    List<GroupUploadFile> files,
  );
  Future<Map<String, dynamic>> getStudyFileLink(
    String groupId,
    String documentId,
    String fileId, {
    bool preview = false,
  });
  Future<Map<String, dynamic>> getStudyOfficePreview(
    String groupId,
    String documentId,
    String fileId,
  );
  Future<Uint8List> downloadStudyBundle(String groupId, String documentId);
  Future<void> deleteStudyDocument(String groupId, String documentId);
  Future<void> reportStudyDocument(
    String groupId,
    String documentId,
    String reason,
  );
  Future<void> moderateStudyDocument(
    String groupId,
    String documentId,
    bool approved,
    String reason,
  );
  Future<List<Map<String, dynamic>>> getStudyDocumentReports(String groupId);
  Future<void> decideStudyDocumentReport(
    String groupId,
    String reportId,
    bool remove,
    String note,
  );
  Future<List<Map<String, dynamic>>> getAdminStudySubjects(
    String groupId,
    String query,
    int offset,
  );
  Future<void> saveStudySubject(String groupId, Map<String, dynamic> payload);
  Future<List<Map<String, dynamic>>> getGroupReports(String groupId);
  Future<void> resolveGroupReport(
    String reportId,
    bool hideContent,
    String note, {
    bool alreadyRemoved = false,
  });
}
