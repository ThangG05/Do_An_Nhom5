import unittest

from src.services.auth_service import (
    GoogleAuthenticationError,
    _normalize_email,
    _validate_google_identity,
)


class GoogleAuthValidationTests(unittest.TestCase):
    def test_normalize_email_lowercases_and_trims(self) -> None:
        self.assertEqual(
            _normalize_email("  Student@HVNH.EDU.VN "),
            "student@hvnh.edu.vn",
        )

    def test_accepts_verified_hvnh_workspace(self) -> None:
        email, full_name, picture = _validate_google_identity(
            {
                "email": "Student@HVNH.EDU.VN",
                "email_verified": True,
                "hd": "hvnh.edu.vn",
                "name": "Nguyễn Văn A",
                "picture": "https://example.com/avatar.jpg",
            }
        )

        self.assertEqual(email, "student@hvnh.edu.vn")
        self.assertEqual(full_name, "Nguyễn Văn A")
        self.assertEqual(picture, "https://example.com/avatar.jpg")

    def test_rejects_untrusted_accounts(self) -> None:
        cases = [
            {"email": "student@gmail.com", "email_verified": True, "hd": "gmail.com"},
            {"email": "student@hvnh.edu.vn", "email_verified": False, "hd": "hvnh.edu.vn"},
            {"email": "student@hvnh.edu.vn", "email_verified": True},
        ]
        for claims in cases:
            with self.subTest(claims=claims):
                with self.assertRaises(GoogleAuthenticationError):
                    _validate_google_identity(claims)


if __name__ == "__main__":
    unittest.main()
