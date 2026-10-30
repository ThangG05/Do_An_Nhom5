import '../../auth_session.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_data_source.dart';
import '../datasources/google_sign_in_data_source.dart';

class AuthRepositoryImpl implements AuthRepository {
  const AuthRepositoryImpl(
    this._remoteDataSource,
    this._googleDataSource,
    this._session,
  );
  final AuthRemoteDataSource _remoteDataSource;
  final GoogleSignInDataSource _googleDataSource;
  final AuthSession _session;

  @override
  Future<bool> hasActiveSession() => _session.isSignedIn;

  @override
  Future<void> signIn({required String email, required String password}) async {
    final response = await _remoteDataSource.login(email, password);
    await _session.save(response);
  }

  @override
  Future<void> signInWithGoogle() async {
    final credential = await _googleDataSource.authenticate();
    await signInWithGoogleCredential(credential);
  }

  @override
  Future<void> initializeGoogleSignIn() => _googleDataSource.initialize();

  @override
  Future<void> signInWithGoogleCredential(String credential) async {
    try {
      final response = await _remoteDataSource.loginWithGoogle(credential);
      await _session.save(response);
    } catch (_) {
      await _googleDataSource.reset();
      rethrow;
    }
  }

  @override
  Future<void> signOut() async {
    final refreshToken = await _session.refreshToken;
    try {
      if (refreshToken != null && refreshToken.isNotEmpty) {
        await _remoteDataSource.logout(refreshToken);
      }
    } catch (_) {
      // Nếu backend đang ngoại tuyến, người dùng vẫn phải thoát được trên máy.
    } finally {
      // Luôn xóa thông tin cục bộ, kể cả khi thiết bị đang ngoại tuyến.
      await _session.clear();
      await _googleDataSource.reset();
    }
  }

  @override
  Future<void> requestRegistrationCode(String email) =>
      _remoteDataSource.requestCode(email);
  @override
  Future<Map<String, dynamic>> verifyRegistrationCode(
    String email,
    String code,
  ) => _remoteDataSource.verifyCode(email, code);
  @override
  Future<void> completeRegistration({
    required String registrationToken,
    required String fullName,
    required String password,
  }) async {
    await _session.save(
      await _remoteDataSource.complete(registrationToken, fullName, password),
    );
  }

  @override
  Future<void> requestPasswordReset(String email) =>
      _remoteDataSource.requestPasswordReset(email);
  @override
  Future<void> resetPassword({
    required String email,
    required String code,
    required String newPassword,
  }) => _remoteDataSource.resetPassword(email, code, newPassword);
}
