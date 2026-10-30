import '../entities/avatar_upload_file.dart';

abstract interface class UserRepository {
  Future<Map<String, dynamic>> getMyProfile();
  Future<Map<String, dynamic>> getProfile(String userId);
  Future<Map<String, dynamic>> updateMyProfile(Map<String, dynamic> changes);
  Future<void> updateMyAvatar(AvatarUploadFile file);
  Future<void> updateMyCover(AvatarUploadFile file);
  Future<List<Map<String, dynamic>>> searchUsers(String query);
  Future<List<Map<String, dynamic>>> getFriends(String userId);
  Future<List<Map<String, dynamic>>> getProfilePosts(String userId);
  Future<List<Map<String, dynamic>>> getProfilePhotos(String userId);
  Future<List<Map<String, dynamic>>> getProfileListings(String userId, {String category = 'all'});
  Future<List<Map<String, dynamic>>> getGroupPosts(String userId);
  Future<List<Map<String, dynamic>>> getBlockedUsers();
  Future<String> updateFriendship(String userId, String action);
  Future<void> setBlocked(String userId, bool blocked);
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  });
}
