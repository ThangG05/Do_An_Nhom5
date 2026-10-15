import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.db.models.user import AccountStatus, SystemRole
from src.services import auth_service, email_service


class AdminPasswordRecoveryTests(unittest.TestCase):
    def test_super_admin_uses_configured_inbox(self) -> None:
        user = SimpleNamespace(email="super-admin@hvnh.edu.vn", system_role=SystemRole.SUPER_ADMIN, id="admin-id")
        db = Mock()
        with patch.object(auth_service.settings, "ADMIN_PASSWORD_RECOVERY_EMAILS", '{"super-admin@hvnh.edu.vn":"owner@example.com"}'):
            self.assertEqual(auth_service._password_reset_recipient(user, db), "owner@example.com")
        db.scalar.assert_not_called()

    def test_group_admin_uses_configured_inbox(self) -> None:
        user = SimpleNamespace(email="admin-hoc-tap@hvnh.edu.vn", system_role=SystemRole.USER, id="group-admin-id")
        db = Mock()
        db.scalar.return_value = 1
        with patch.object(auth_service.settings, "ADMIN_PASSWORD_RECOVERY_EMAILS", '{"admin-hoc-tap@hvnh.edu.vn":"group-owner@example.com"}'):
            self.assertEqual(auth_service._password_reset_recipient(user, db), "group-owner@example.com")
        db.scalar.assert_called_once()

    def test_mapping_cannot_redirect_regular_user(self) -> None:
        user = SimpleNamespace(email="student@hvnh.edu.vn", system_role=SystemRole.USER, id="student-id")
        db = Mock()
        db.scalar.return_value = None
        with patch.object(auth_service.settings, "ADMIN_PASSWORD_RECOVERY_EMAILS", '{"student@hvnh.edu.vn":"other@example.com"}'):
            self.assertEqual(auth_service._password_reset_recipient(user, db), user.email)

    def test_invalid_config_fails_closed(self) -> None:
        user = SimpleNamespace(email="super-admin@hvnh.edu.vn", system_role=SystemRole.SUPER_ADMIN, id="admin-id")
        with patch.object(auth_service.settings, "ADMIN_PASSWORD_RECOVERY_EMAILS", "not-json"):
            with self.assertRaises(email_service.EmailDeliveryError):
                auth_service._password_reset_recipient(user, Mock())

    def test_reset_code_is_sent_to_admin_recovery_inbox(self) -> None:
        user = SimpleNamespace(id=uuid.uuid4(), email="super-admin@hvnh.edu.vn", status=AccountStatus.ACTIVE,
                               deleted_at=None, system_role=SystemRole.SUPER_ADMIN)
        db = Mock()
        db.scalar.side_effect = [user, None]
        with patch.object(auth_service.settings, "ADMIN_PASSWORD_RECOVERY_EMAILS", '{"super-admin@hvnh.edu.vn":"owner@example.com"}'), \
             patch.object(auth_service.email_service, "send_password_reset_code") as send:
            auth_service.request_password_reset(user.email, db)
        self.assertEqual(send.call_args.args[0], "owner@example.com")
        self.assertEqual(send.call_args.kwargs["account_email"], user.email)
        self.assertRegex(send.call_args.args[1], r"^[0-9]{4}$")
        db.commit.assert_called_once()

    def test_admin_change_password_checks_current_password_and_revokes_refresh(self) -> None:
        user = SimpleNamespace(id=uuid.uuid4(), password_hash="old-hash", system_role=SystemRole.SUPER_ADMIN)
        db = Mock()
        with patch.object(auth_service, "verify_password", side_effect=[True, False]), \
             patch.object(auth_service, "hash_password", return_value="new-hash"):
            auth_service.change_password(user, "OldPassword1", "NewPassword2", db)
        self.assertEqual(user.password_hash, "new-hash")
        db.execute.assert_called_once()
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
