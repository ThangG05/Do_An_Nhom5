import unittest

from src.core.security import (
    create_registration_token,
    create_access_token,
    decode_access_token,
    decode_registration_token,
    hash_password,
    hash_refresh_token,
    hash_verification_code,
    verification_code_matches,
    verify_password,
)


class AuthSecurityTests(unittest.TestCase):
    def test_password_is_hashed_and_verifiable(self) -> None:
        encoded = hash_password("MatKhau123")

        self.assertNotEqual(encoded, "MatKhau123")
        self.assertTrue(verify_password("MatKhau123", encoded))
        self.assertFalse(verify_password("SaiMatKhau123", encoded))

    def test_placeholder_password_cannot_authenticate(self) -> None:
        self.assertFalse(verify_password("anything", "!google:placeholder"))
        self.assertFalse(verify_password("anything", "!pending:placeholder"))

    def test_verification_code_is_bound_to_user(self) -> None:
        code_hash = hash_verification_code("user-1", "1234")

        self.assertTrue(verification_code_matches("user-1", "1234", code_hash))
        self.assertFalse(verification_code_matches("user-2", "1234", code_hash))
        self.assertFalse(verification_code_matches("user-1", "9999", code_hash))

    def test_registration_token_round_trip(self) -> None:
        token, expires_in = create_registration_token("user-1")

        self.assertGreater(expires_in, 0)
        self.assertEqual(decode_registration_token(token), "user-1")

    def test_access_token_round_trip(self) -> None:
        token, expires_in = create_access_token("user-1")

        self.assertGreater(expires_in, 0)
        self.assertEqual(decode_access_token(token), "user-1")

    def test_refresh_token_hash_is_deterministic(self) -> None:
        self.assertEqual(hash_refresh_token("token"), hash_refresh_token("token"))
        self.assertNotEqual(hash_refresh_token("token"), hash_refresh_token("other"))


if __name__ == "__main__":
    unittest.main()
