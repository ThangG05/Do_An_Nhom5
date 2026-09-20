from dataclasses import dataclass

from app.rag.reranker import HeuristicReranker, RerankContext


@dataclass
class Hit:
    chunk_id: str
    title: str
    content: str
    academic_year: str | None = None
    published_at: str | None = None


def test_reranker_promotes_exact_named_entity() -> None:
    semantic = Hit("semantic", "Danh sách giảng viên", "Thông tin khoa Công nghệ thông tin")
    exact = Hit("exact", "Giảng viên | Triệu Thu Hương", "Hồ sơ chính thức")
    ranked = HeuristicReranker().rerank(
        [semantic, exact], RerankContext("Giảng viên Triệu Thu Hương là ai?"),
        {"semantic": 0.02, "exact": 0.016},
    )
    assert ranked[0].chunk_id == "exact"


def test_reranker_promotes_requested_academic_year() -> None:
    old = Hit("old", "Mức thu học phí", "Học phí", "2023/2024")
    requested = Hit("requested", "Mức thu học phí", "Học phí", "2024/2025")
    ranked = HeuristicReranker().rerank(
        [old, requested], RerankContext("Học phí 2024/2025", "2024/2025"),
        {"old": 0.02, "requested": 0.019},
    )
    assert ranked[0].chunk_id == "requested"


def test_explicit_current_query_prioritizes_newest_publication() -> None:
    old = Hit("old", "Mức thu học phí hiện tại", "Mức thu học phí", "2023/2024",
              "2024-01-08T00:00:00+07:00")
    newest = Hit("newest", "Mức thu học phí", "Mức thu học phí", "2025/2026",
                 "2025-07-01T00:00:00+07:00")
    ranked = HeuristicReranker().rerank(
        [old, newest], RerankContext("Mức thu học phí hiện tại là bao nhiêu?", latest=True),
        {"old": 0.03, "newest": 0.01},
    )
    assert ranked[0].chunk_id == "newest"


def test_reranker_promotes_numeric_evidence_for_amount_question() -> None:
    preamble = Hit("preamble", "Mức thu học phí", "Quyết định áp dụng trong năm học.")
    table = Hit("table", "Mức thu học phí", "Khối III: 785.000 đồng/tín chỉ.")
    ranked = HeuristicReranker().rerank(
        [preamble, table], RerankContext("Mức thu học phí là bao nhiêu?"),
        {"preamble": 0.02, "table": 0.019},
    )
    assert ranked[0].chunk_id == "table"


def test_reranker_promotes_procedure_evidence_for_login_question() -> None:
    general = Hit("general", "Hướng dẫn LMS", "Học viện triển khai hệ thống LMS.")
    steps = Hit("steps", "Hướng dẫn LMS", "Bước 1 đăng nhập; chọn My Courses.")
    ranked = HeuristicReranker().rerank(
        [general, steps], RerankContext("Đăng nhập và truy cập LMS như thế nào?"),
        {"general": 0.02, "steps": 0.019},
    )
    assert ranked[0].chunk_id == "steps"


def test_reranker_matches_ascii_pdf_tuition_title_and_demotes_service_fee() -> None:
    tuition = Hit("tuition", "QD 3455 Muc thu hoc phi nam hoc 2025 2026.pdf",
                  "785.000 đồng/tín chỉ")
    service = Hit("service", "QD 3456 Muc thu dich vu nam hoc 2025 2026.pdf",
                  "900.000 đồng/lần")
    ranked = HeuristicReranker().rerank(
        [service, tuition], RerankContext("Mức thu học phí năm học 2025/2026"),
        {"service": 0.02, "tuition": 0.02},
    )
    assert ranked[0].chunk_id == "tuition"


def test_reranker_promotes_scholarship_notice_over_generic_student_content() -> None:
    scholarship = Hit(
        "scholarship",
        "TB ve xet Hoc bong KKHT chuong trinh CLC va Qte.pdf",
        "Thong bao dieu kien va danh sach xet hoc bong khuyen khich hoc tap.",
        "2024/2025",
    )
    generic = Hit(
        "generic",
        "Thong bao danh cho sinh vien",
        "Thong tin tuyen sinh va hoc phi nam hoc 2025/2026.",
        "2025/2026",
    )
    ranked = HeuristicReranker().rerank(
        [generic, scholarship],
        RerankContext("Dieu kien xet hoc bong khuyen khich hoc tap la gi?"),
        {"generic": 0.03, "scholarship": 0.015},
    )
    assert ranked[0].chunk_id == "scholarship"
