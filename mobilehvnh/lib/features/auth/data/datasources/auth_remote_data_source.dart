import '../../../../core/api_client.dart';

class AuthRemoteDataSource {
  const AuthRemoteDataSource(this._apiClient);
  final ApiClient _apiClient;

  Future<Map<String, dynamic>> login(String email, String password) =>
      _apiClient.post('/auth/login', {'email': email, 'password': password});
  Future<Map<String, dynamic>> loginWithGoogle(String credential) =>
      _apiClient.post('/auth/google', {'credential': credential});
  Future<void> requestCode(String email) async {
    await _apiClient.post('/auth/register/request-code', {'email': email});
  }

  Future<Map<String, dynamic>> verifyCode(String email, String code) =>
      _apiClient.post('/auth/register/verify-code', {
        'email': email,
        'code': code,
      });
  Future<Map<String, dynamic>> complete(
    String token,
    String name,
    String password,
  ) => _apiClient.post('/auth/register/complete', {
    'registration_token': token,
    'full_name': name,
    'password': password,
  });
  Future<void> requestPasswordReset(String email) async =>
      _apiClient.post('/auth/password/forgot', {'email': email});
  Future<void> resetPassword(
    String email,
    String code,
    String newPassword,
  ) async => _apiClient.post('/auth/password/reset', {
    'email': email,
    'code': code,
    'new_password': newPassword,
  });

  Future<void> logout(String refreshToken) async {
    await _apiClient.post('/auth/logout', {'refresh_token': refreshToken});
  }
}
