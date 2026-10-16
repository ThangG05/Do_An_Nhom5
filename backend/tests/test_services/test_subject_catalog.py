import json
from pathlib import Path
import re
from collections import defaultdict

from src.models.study_document import SubjectUpsertRequest


def test_catalog_preserves_source_rows_and_all_major_links():
    root = Path(__file__).resolve().parents[2]
    data = json.loads((root / "alembic/data/hvnh_catalog_20261016.json").read_text(encoding="utf-8"))
    source = (root.parent / "danh_muc_hoc_phan_HVNH_va_thiet_ke_database.md").read_text(encoding="utf-8")
    subjects, links, majors = set(), set(), set()
    category = major = None
    for line in source.splitlines():
        if line.startswith("## 2."):
            category, major = "GENERAL", None
        if line.startswith("## 4."):
            category = None
        header = re.match(r"### 3\.\d+\. (.+) — mã ngành: `([^`]+)`", line)
        if header:
            major = header[1]
            majors.add((major, None if header[2] == "Chưa có" else header[2]))
            category = "SPECIALIZED"
        row = re.match(r"\| \d+ \| ([^|]+) \| ([^|]+) \|$", line)
        if row and category:
            code = None if row[1].strip() == "—" else row[1].strip()
            name = row[2].strip()
            subjects.add((code, name, category))
            if major:
                links.add((major, code, name))
    assert len(subjects) == 355
    assert len(links) == 481
    assert len(majors) == 18
    assert subjects == {(s["code"], s["name"], s["category"]) for s in data["subjects"]}
    assert links == {(l["major"], l["code"], l["name"]) for l in data["links"]}
    assert majors == {(m["name"], m["code"]) for m in data["majors"]}
    names = defaultdict(set)
    for subject in data["subjects"]:
        if subject["code"]:
            names[subject["code"]].add(subject["name"])
    assert sum(len(values) > 1 for values in names.values()) == 20
    assert sum(s["code"] is None for s in data["subjects"]) == 3


def test_missing_codes_are_supported_without_inventing_a_code():
    request = SubjectUpsertRequest(name="Thương mại điện tử", source_note="Tài liệu người dùng cung cấp")
    assert request.code is None
