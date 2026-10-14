"""Structured group posts: new web forms and legacy mobile compatibility."""
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.db.models.post import Post, PostStatus, PostVisibility
from src.models.group import GroupPostCreateRequest
from src.models.post import CreateProfilePostRequest, MarketListingData, UpdatePostRequest
from src.services import group_service, post_service


CASES = [
    ("market", "pass-do", "marketListing", {"productName": "Bàn phím", "price": "0", "location": "Hà Nội"}, ""),
    ("event", "su-kien", "eventListing", {"eventName": "Ngày hội", "eventDate": "2026-12-20", "eventTime": "18:00", "location": "Hội trường"}, "Giao lưu sinh viên"),
    ("roommate", "ghep-phong-tim-tro", "roomListing", {"rentPerMonth": "", "location": "Chùa Bộc"}, "Tìm bạn cùng phòng"),
    ("study", "hoc-tap", "studyListing", {"subjectName": "Giải tích 1"}, "Tổng hợp kiến thức chương 1"),
]


@pytest.mark.parametrize("category,slug,field,details,content", CASES)
def test_each_type_can_be_created_without_attachments(category, slug, field, details, content):
    payload = CreateProfilePostRequest(form_version=2, category=category, content=content, **{field: details})
    assert payload.media_ids == []
    stored = post_service._listing_data(payload, category)
    assert stored["_form_version"] == 2
    for key, value in details.items():
        assert stored[key] == value


@pytest.mark.parametrize("category,slug,field,details,content", CASES)
def test_direct_group_endpoint_persists_details_and_moderation(category, slug, field, details, content):
    db = Mock()
    user = SimpleNamespace(id=uuid.uuid4())
    group_id = uuid.uuid4()
    payload = GroupPostCreateRequest(form_version=2, content=content, **{field: details})
    with patch.object(group_service, "_group", return_value={"slug": slug}), patch.object(group_service, "_membership", return_value="MEMBER"), patch.object(group_service, "_serialize", return_value="created"), patch("src.services.system_service.enforce_content"):
        assert group_service.create_post(db, group_id, user, payload) == "created"
    post = db.add.call_args.args[0]
    assert isinstance(post, Post)
    assert post.category == category and post.group_id == group_id
    assert post.status == PostStatus.PENDING
    assert post.listing_data["_form_version"] == 2
    assert all(post.listing_data[k] == v for k, v in details.items())
    db.commit.assert_called_once()


@pytest.mark.parametrize("price", ["", "-1", "1.5", "Thỏa thuận", "1000000000000000"])
def test_market_rejects_invalid_prices(price):
    with pytest.raises(ValidationError):
        CreateProfilePostRequest(form_version=2, category="market", marketListing={"productName": "Máy tính", "price": price, "location": "Hà Nội"})


@pytest.mark.parametrize("field", ["productName", "location"])
def test_market_rejects_whitespace_required_fields(field):
    details = {"productName": "Máy tính", "price": "1000", "location": "Hà Nội", field: "  "}
    with pytest.raises(ValidationError):
        CreateProfilePostRequest(form_version=2, category="market", marketListing=details)


@pytest.mark.parametrize("category,slug,field,details,content", CASES[1:])
def test_attachment_cannot_replace_required_description(category, slug, field, details, content):
    with pytest.raises(ValidationError):
        CreateProfilePostRequest(form_version=2, category=category, content="  ", media_ids=[uuid.uuid4()], **{field: details})


@pytest.mark.parametrize("day,hour", [("2026-02-30", "18:00"), ("2026-12-20", "25:00"), ("", "" )])
def test_event_rejects_invalid_datetime(day, hour):
    with pytest.raises(ValidationError):
        CreateProfilePostRequest(form_version=2, category="event", content="Mô tả", eventListing={"eventName": "Sự kiện", "eventDate": day, "eventTime": hour, "location": "Hà Nội"})


def test_legacy_mobile_and_old_listing_rows_still_work():
    assert GroupPostCreateRequest(content="Bài cũ").form_version == 1
    assert CreateProfilePostRequest(category="event", content="Bài cũ").eventListing is None
    assert MarketListingData(price="Thỏa thuận").productName == ""


def test_direct_group_rejects_details_for_wrong_group():
    db = Mock()
    payload = GroupPostCreateRequest(form_version=2, content="Mô tả", marketListing={"productName": "Máy tính", "price": "0", "location": "Hà Nội"})
    with patch.object(group_service, "_group", return_value={"slug": "hoc-tap"}), patch.object(group_service, "_membership", return_value="MEMBER"), pytest.raises(HTTPException) as caught:
        group_service.create_post(db, uuid.uuid4(), SimpleNamespace(id=uuid.uuid4()), payload)
    assert caught.value.status_code == 422
    db.add.assert_not_called()


def test_nonmember_cannot_create_structured_post():
    db = Mock()
    with patch.object(group_service, "_group", return_value={"slug": "hoc-tap"}), patch.object(group_service, "_membership", return_value=None), pytest.raises(HTTPException) as caught:
        group_service.create_post(db, uuid.uuid4(), SimpleNamespace(id=uuid.uuid4()), GroupPostCreateRequest(content="Không có quyền"))
    assert caught.value.status_code == 403
    db.add.assert_not_called()


def test_new_market_can_update_empty_optional_description_without_losing_title():
    user = SimpleNamespace(id=uuid.uuid4())
    post = Post(id=uuid.uuid4(), author_id=user.id, group_id=uuid.uuid4(), category="market", content="", status=PostStatus.APPROVED, visibility=PostVisibility.PUBLIC, listing_data={"_form_version": 2, "productName": "Bàn phím", "price": "0", "location": "Hà Nội"})
    db = Mock(); db.get.return_value = post
    with patch.object(post_service, "_serialize", return_value="updated"), patch("src.services.system_service.enforce_content"):
        assert post_service.update_post(db, post.id, user, UpdatePostRequest(content="")) == "updated"
    assert post.listing_data["productName"] == "Bàn phím"
    assert post.status == PostStatus.PENDING


def test_cannot_move_existing_post_to_different_group():
    user = SimpleNamespace(id=uuid.uuid4())
    db = Mock(); db.get.return_value = Post(author_id=user.id, group_id=uuid.uuid4(), category="study")
    with pytest.raises(HTTPException) as caught:
        post_service.update_post(db, uuid.uuid4(), user, UpdatePostRequest(content="Nội dung", category="market"))
    assert caught.value.status_code == 422
    db.commit.assert_not_called()


def test_media_count_limit_is_enforced_server_side():
    with pytest.raises(ValidationError):
        GroupPostCreateRequest(content="Tài liệu", media_ids=[uuid.uuid4() for _ in range(11)])


@pytest.mark.parametrize("category,slug,field,details,content", CASES)
def test_serialization_returns_each_category_details(category, slug, field, details, content):
    user = SimpleNamespace(id=uuid.uuid4(), username="student", profile=None)
    post = Post(id=uuid.uuid4(), author_id=user.id, category=category, content=content,
                listing_data={**details, "_form_version": 2}, status=PostStatus.APPROVED,
                visibility=PostVisibility.PUBLIC, created_at=datetime.now(timezone.utc), is_pinned=False)
    db = Mock()
    db.get.side_effect = lambda model, key: user if key == user.id else None
    db.scalars.return_value.all.return_value = []
    db.scalar.return_value = 0
    result = post_service._serialize(db, post, user.id).model_dump()
    assert all(result[field][key] == value for key, value in details.items())
