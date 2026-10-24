import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import Mock, patch

from src.db.models.post import PostVisibility
from src.services.post_service import _can_view


class PostVisibilityTests(unittest.TestCase):
    def setUp(self):
        self.author=uuid.uuid4();self.viewer=uuid.uuid4();self.db=Mock()
        self.blocked = patch('src.services.post_service.is_blocked', return_value=False).start()
        self.addCleanup(patch.stopall)

    def post(self,visibility):
        return SimpleNamespace(author_id=self.author,visibility=visibility,group_id=None,category='general')

    def test_block_overrides_public_visibility(self):
        self.blocked.return_value = True
        self.assertFalse(_can_view(self.db, self.post(PostVisibility.PUBLIC), self.viewer))

    def test_block_overrides_friendship(self):
        self.blocked.return_value = True
        self.db.scalar.return_value = True
        self.assertFalse(_can_view(self.db, self.post(PostVisibility.FRIENDS), self.viewer))

    def test_public_post_is_visible(self):
        self.assertTrue(_can_view(self.db,self.post(PostVisibility.PUBLIC),self.viewer))

    def test_owner_can_view_private_post(self):
        self.assertTrue(_can_view(self.db,self.post(PostVisibility.PRIVATE),self.author))

    def test_stranger_cannot_view_private_post(self):
        self.assertFalse(_can_view(self.db,self.post(PostVisibility.PRIVATE),self.viewer))

    def test_friends_visibility_checks_friendship(self):
        self.db.scalar.return_value=True
        self.assertTrue(_can_view(self.db,self.post(PostVisibility.FRIENDS),self.viewer))
        self.db.scalar.return_value=False
        self.assertFalse(_can_view(self.db,self.post(PostVisibility.FRIENDS),self.viewer))


if __name__=="__main__":unittest.main()
