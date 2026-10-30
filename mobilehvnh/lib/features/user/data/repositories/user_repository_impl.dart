import 'dart:typed_data';

import 'package:file_picker/file_picker.dart';

import '../../domain/entities/avatar_upload_file.dart';
import '../../domain/repositories/user_repository.dart';
import '../datasources/user_remote_data_source.dart';

class UserRepositoryImpl implements UserRepository {
  const UserRepositoryImpl(this._remote);
  final UserRemoteDataSource _remote;

  PlatformFile _platformFile(AvatarUploadFile file) => PlatformFile(
        name: file.name,
        size: file.size,
        path: file.path,
        bytes: file.bytes == null ? null : Uint8List.fromList(file.bytes!),
      );

  Future<List<Map<String, dynamic>>> _maps(Future<List<dynamic>> source) async =>
      (await source).map((value) => Map<String, dynamic>.from(value as Map)).toList();

  @override
  Future<Map<String, dynamic>> getMyProfile() => _remote.me();

  @override
  Future<Map<String, dynamic>> getProfile(String userId) => _remote.profile(userId);

  @override
  Future<Map<String, dynamic>> updateMyProfile(Map<String, dynamic> changes) => _remote.update(changes);

  @override
  Future<void> updateMyAvatar(AvatarUploadFile file) => _remote.updateAvatar(_platformFile(file));

  @override
  Future<void> updateMyCover(AvatarUploadFile file) => _remote.updateCover(_platformFile(file));

  @override
  Future<List<Map<String, dynamic>>> searchUsers(String query) => _maps(_remote.search(query));

  @override
  Future<List<Map<String, dynamic>>> getFriends(String userId) => _maps(_remote.friends(userId));

  @override
  Future<List<Map<String, dynamic>>> getProfilePosts(String userId) => _maps(_remote.posts(userId));

  @override
  Future<List<Map<String, dynamic>>> getProfilePhotos(String userId) => _maps(_remote.photos(userId));

  @override
  Future<List<Map<String, dynamic>>> getProfileListings(String userId, {String category = 'all'}) =>
      _maps(_remote.listings(userId, category: category));

  @override
  Future<List<Map<String, dynamic>>> getGroupPosts(String userId) => _maps(_remote.groupPosts(userId));

  @override
  Future<List<Map<String, dynamic>>> getBlockedUsers() => _maps(_remote.blocked());

  @override
  Future<String> updateFriendship(String userId, String action) async =>
      (await _remote.friendship(userId, action))['status']?.toString() ?? 'none';

  @override
  Future<void> setBlocked(String userId, bool blocked) => _remote.setBlocked(userId, blocked);

  @override
  Future<void> changePassword({required String currentPassword, required String newPassword}) =>
      _remote.changePassword(currentPassword: currentPassword, newPassword: newPassword);
}
