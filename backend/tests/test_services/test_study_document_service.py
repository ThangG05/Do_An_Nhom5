import io
import uuid
import zipfile
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi import HTTPException, UploadFile

from src.services import study_document_service as library


def _upload(name: str, content: bytes, mime: str) -> UploadFile:
    return UploadFile(file=io.BytesIO(content), filename=name,
                      headers={"content-type": mime})


@pytest.mark.parametrize("name,mime", [
    ("virus.exe", "application/octet-stream"),
    ("data.zip", "application/zip"),
    ("photo.png", "image/png"),
])
def test_rejects_disallowed_or_forged_file(name, mime):
    with pytest.raises(HTTPException) as exc:
        library._validate_file(_upload(name, b"not a valid document", mime))
    assert exc.value.status_code == 400


def test_validates_ooxml_content_not_just_extension():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    valid = library._validate_file(_upload(
        "lesson.docx", stream.getvalue(), library.MIME_BY_EXTENSION["docx"]))
    assert valid["size"] == len(stream.getvalue())
    with pytest.raises(HTTPException):
        library._validate_file(_upload(
            "lesson.xlsx", stream.getvalue(), library.MIME_BY_EXTENSION["xlsx"]))


def test_rejects_file_larger_than_limit_without_reading_it_all(monkeypatch):
    monkeypatch.setattr(library, "MAX_SHARE_BYTES", 5)
    with pytest.raises(HTTPException) as exc:
        library._validate_file(_upload("sample.pdf", b"%PDF-1234", "application/pdf"))
    assert exc.value.status_code == 400


def test_private_bucket_must_be_separate(monkeypatch):
    monkeypatch.setattr(library.settings, "R2_BUCKET_NAME", "public-media")
    monkeypatch.setattr(library.settings, "R2_STUDY_BUCKET_NAME", "public-media")
    with pytest.raises(HTTPException) as exc:
        library._private_bucket()
    assert exc.value.status_code == 503
    monkeypatch.setattr(library.settings, "R2_STUDY_BUCKET_NAME", "private-study")
    assert library._private_bucket() == "private-study"


def test_only_study_group_is_eligible():
    group_id = uuid.uuid4()
    db = Mock()
    db.execute.return_value.scalar_one_or_none.return_value = "su-kien"
    with pytest.raises(HTTPException) as exc:
        library.require_study_group(db, group_id)
    assert exc.value.status_code == 404


def test_pending_file_is_not_downloadable_by_other_member(monkeypatch):
    group_id, document_id, file_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    owner = uuid.uuid4()
    db = Mock()
    db.execute.side_effect = [
        SimpleNamespace(scalar_one_or_none=lambda: "hoc-tap"),
        SimpleNamespace(mappings=lambda: SimpleNamespace(first=lambda: {
            "r2_object_key": "study-groups/private.pdf", "original_name": "private.pdf",
            "mime_type": "application/pdf", "status": "PENDING", "uploaded_by": owner,
        })),
        SimpleNamespace(scalar_one_or_none=lambda: "MEMBER"),
    ]
    user = SimpleNamespace(id=uuid.uuid4(), system_role="USER")
    with pytest.raises(HTTPException) as exc:
        library.file_download(db, group_id, document_id, file_id, user)
    assert exc.value.status_code == 404
