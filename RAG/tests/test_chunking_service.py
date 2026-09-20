from app.knowledge.chunking import _pages_for


def test_page_mapping_for_overlapping_chunk() -> None:
    metadata = {"page_ranges": [[1, 0, 100], [2, 102, 200]]}
    assert _pages_for(metadata, 80, 130) == (1, 2)
    assert _pages_for(metadata, 202, 220) == (None, None)
