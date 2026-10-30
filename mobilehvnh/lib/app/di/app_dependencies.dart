import '../../core/api_client.dart';
import '../../features/auth/auth_session.dart';
import '../../features/auth/data/datasources/auth_remote_data_source.dart';
import '../../features/auth/data/datasources/google_sign_in_data_source.dart';
import '../../features/auth/data/repositories/auth_repository_impl.dart';
import '../../features/auth/domain/usecases/sign_in.dart';
import '../../features/auth/domain/repositories/auth_repository.dart';
import '../../features/feed/data/datasources/feed_remote_data_source.dart';
import '../../features/feed/data/repositories/feed_repository_impl.dart';
import '../../features/feed/domain/repositories/feed_repository.dart';
import '../../features/groups/data/datasources/group_remote_data_source.dart';
import '../../features/groups/data/repositories/group_repository_impl.dart';
import '../../features/groups/domain/repositories/group_repository.dart';
import '../../features/chat/data/datasources/chat_remote_data_source.dart';
import '../../features/chat/data/repositories/chat_repository_impl.dart';
import '../../features/chat/domain/repositories/chat_repository.dart';
import '../../features/notifications/data/datasources/notification_remote_data_source.dart';
import '../../features/notifications/data/repositories/notification_repository_impl.dart';
import '../../features/notifications/domain/repositories/notification_repository.dart';
import '../../features/user/data/datasources/user_remote_data_source.dart';
import '../../features/user/data/repositories/user_repository_impl.dart';
import '../../features/user/domain/repositories/user_repository.dart';
import '../../features/ai/data/repositories/ai_repository_impl.dart';
import '../../features/ai/domain/repositories/ai_repository.dart';
import '../../features/admin/data/datasources/admin_remote_data_source.dart';
import '../../features/admin/data/repositories/admin_repository_impl.dart';
import '../../features/admin/domain/repositories/admin_repository.dart';

/// Composition root: infrastructure is created once and injected into features.
class AppDependencies {
  AppDependencies._({
    required this.session,
    required this.apiClient,
    required this.authRepository,
    required this.signIn,
    required this.feedRepository,
    required this.groupRepository,
    required this.chatRepository,
    required this.notificationRepository,
    required this.userRepository,
    required this.aiRepository,
    required this.adminRepository,
  });

  factory AppDependencies.create() {
    final session = AuthSession();
    final apiClient = ApiClient(
      () => session.accessToken,
      refreshTokenProvider: () => session.refreshToken,
      onSessionRefreshed: session.save,
    );
    final authRepository = AuthRepositoryImpl(
      AuthRemoteDataSource(apiClient),
      GoogleSignInDataSource(apiClient),
      session,
    );
    return AppDependencies._(
      session: session,
      apiClient: apiClient,
      authRepository: authRepository,
      signIn: SignIn(authRepository),
      feedRepository: FeedRepositoryImpl(FeedRemoteDataSource(apiClient)),
      groupRepository: GroupRepositoryImpl(GroupRemoteDataSource(apiClient)),
      chatRepository: ChatRepositoryImpl(ChatRemoteDataSource(apiClient)),
      notificationRepository: NotificationRepositoryImpl(
        NotificationRemoteDataSource(apiClient),
      ),
      userRepository: UserRepositoryImpl(UserRemoteDataSource(apiClient)),
      aiRepository: AiRepositoryImpl(apiClient),
      adminRepository: AdminRepositoryImpl(AdminRemoteDataSource(apiClient)),
    );
  }

  final AuthSession session;
  final ApiClient apiClient;
  final AuthRepository authRepository;
  final SignIn signIn;
  final FeedRepository feedRepository;
  final GroupRepository groupRepository;
  final ChatRepository chatRepository;
  final NotificationRepository notificationRepository;
  final UserRepository userRepository;
  final AiRepository aiRepository;
  final AdminRepository adminRepository;
}
