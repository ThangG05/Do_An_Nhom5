abstract interface class AuthRepository {
  Future<void> signIn({required String email, required String password});
  Future<void> signInWithGoogle();
  Future<void> initializeGoogleSignIn();
  Future<void> signInWithGoogleCredential(String credential);
  Future<bool> hasActiveSession();
  Future<void> signOut();
  Future<void> requestRegistrationCode(String email);
  Future<Map<String, dynamic>> verifyRegistrationCode(
    String email,
    String code,
  );
  Future<void> completeRegistration({
    required String registrationToken,
    required String fullName,
    required String password,
  });
  Future<void> requestPasswordReset(String email);
  Future<void> resetPassword({
    required String email,
    required String code,
    required String newPassword,
  });
}
