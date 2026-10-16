from src.db.metadata import target_metadata


def test_combined_metadata_contains_software_and_rag_tables() -> None:
    expected = {
        "users",
        "posts",
        "groups",
        "group_join_requests",
        "system_settings",
        "blacklist_keywords",
        "request_rate_limits",
        "ai_documents",
        "ai_document_chunks",
        "ai_conversations",
        "ai_messages",
        "subjects",
        "majors",
        "major_subjects",
        "study_documents",
        "study_document_files",
        "rag_token_usage",
    }

    assert expected.issubset(target_metadata.tables)
    assert len(target_metadata.tables) == 46
