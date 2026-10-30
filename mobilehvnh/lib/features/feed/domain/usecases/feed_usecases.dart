import '../entities/upload_file.dart';
import '../repositories/feed_repository.dart';

class GetFeed {
  const GetFeed(this.repository);
  final FeedRepository repository;
  Future<List<Map<String, dynamic>>> call() => repository.getFeed();
}

class CreatePost {
  const CreatePost(this.repository);
  final FeedRepository repository;
  Future<void> call(String content, List<UploadFile> files) =>
      repository.createPost(content: content, files: files);
}

class SetPostLike {
  const SetPostLike(this.repository);
  final FeedRepository repository;
  Future<Map<String, dynamic>> call(String id, bool liked) =>
      repository.setLike(id, liked);
}
