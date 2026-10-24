"""Uses the rollback-only integration fixtures; never persists test accounts/posts."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from src.db.models.post import Post, PostStatus, PostType, PostVisibility


@pytest.mark.parametrize("reverse", [False, True])
def test_block_prevents_direct_post_reads_and_interactions(client, db_session, make_user, auth_headers, reverse):
    author, viewer = make_user(), make_user()
    post = Post(author_id=author.id, content="Blocked public post", category="general",
                post_type=PostType.PROFILE_POST, visibility=PostVisibility.PUBLIC, status=PostStatus.APPROVED)
    db_session.add(post)
    db_session.flush()
    blocker, blocked = (viewer, author) if reverse else (author, viewer)
    db_session.execute(text("INSERT INTO user_blocks(blocker_id,blocked_id) VALUES(:a,:b)"), {"a": blocker.id, "b": blocked.id})
    db_session.commit()
    url = f"/api/v1/posts/{post.id}"
    headers = auth_headers(viewer)
    assert client.get(url, headers=headers).status_code == 403
    assert client.get(url + "/comments", headers=headers).status_code == 403
    assert client.put(url + "/like", headers=headers, json={"is_liked": True}).status_code == 403
    assert client.post(url + "/comments", headers=headers, json={"content": "not allowed"}).status_code == 403
    assert db_session.scalar(text("SELECT count(*) FROM post_likes WHERE post_id=:pid"), {"pid": post.id}) == 0
    assert db_session.scalar(text("SELECT count(*) FROM comments WHERE post_id=:pid"), {"pid": post.id}) == 0


def test_paged_posts_are_stable_filtered_and_do_not_leak_other_groups(client, db_session, make_user, auth_headers, active_group):
    owner, outsider = make_user(), make_user()
    gid = active_group["id"]
    marker = f"pagination-{uuid.uuid4()}"
    db_session.execute(text("INSERT INTO group_members(group_id,user_id,role) VALUES(:gid,:uid,'MEMBER')"), {"gid": gid, "uid": owner.id})
    now = datetime.now(timezone.utc)
    for index in range(13):
        db_session.add(Post(author_id=owner.id, group_id=gid, content=f"{marker} {index}", category="study",
                            post_type=PostType.STANDARD, visibility=PostVisibility.PUBLIC,
                            status=PostStatus.APPROVED, created_at=now))
    db_session.add(Post(author_id=owner.id, content="personal", category="general", post_type=PostType.PROFILE_POST,
                        visibility=PostVisibility.PRIVATE, status=PostStatus.APPROVED, created_at=now))
    db_session.commit()
    headers = auth_headers(owner)
    paths = [f"/api/v1/groups/{gid}/posts?q={marker}&", f"/api/v1/groups/{gid}/posts/mine?",
             f"/api/v1/users/{owner.id}/posts?filter=study&", f"/api/v1/users/{owner.id}/group-posts?"]
    for path in paths:
        first = client.get(path + "limit=10&offset=0", headers=headers)
        second = client.get(path + "limit=10&offset=10", headers=headers)
        assert first.status_code == second.status_code == 200, (first.text, second.text)
        assert len(first.json()) == 10
        assert len(second.json()) == 3
        assert {row["id"] for row in first.json()}.isdisjoint(row["id"] for row in second.json())
        assert client.get(path + "limit=10&offset=0", headers=headers).json() == first.json()
        assert client.get(path + "limit=101", headers=headers).status_code == 422
        assert client.get(path + "offset=-1", headers=headers).status_code == 422
    outsider_headers = auth_headers(outsider)
    assert client.get(f"/api/v1/groups/{gid}/posts?limit=10", headers=outsider_headers).status_code == 403
    assert client.get(f"/api/v1/users/{owner.id}/posts?limit=10", headers=outsider_headers).json() == []
