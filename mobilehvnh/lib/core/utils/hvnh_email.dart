final hvnhStudentEmailPattern = RegExp(
  r'^[a-z0-9][a-z0-9._-]{7,63}@hvnh\.edu\.vn$',
  caseSensitive: false,
);

bool isValidHvnhEmail(String? value) {
  if (value == null) return false;
  final email = value.trim();
  return hvnhStudentEmailPattern.hasMatch(email) ||
      RegExp(
        r'^(admin|root)@hvnh\.edu\.vn$',
        caseSensitive: false,
      ).hasMatch(email);
}
