"""Read-only catalog check: python -m scripts.verify_study_catalog."""
from sqlalchemy import text
from src.db.session import SessionLocal


def main():
    with SessionLocal() as db:
        for label, sql in {
            "migration": "SELECT version_num FROM alembic_version",
            "majors": "SELECT count(*) FROM majors",
            "subjects": "SELECT count(*) FROM subjects",
            "general": "SELECT count(*) FROM subjects WHERE category='GENERAL'",
            "major_subject_links": "SELECT count(*) FROM major_subjects",
            "missing_subject_codes": "SELECT count(*) FROM subjects WHERE code IS NULL",
            "missing_major_codes": "SELECT count(*) FROM majors WHERE code IS NULL",
            "conflicting_codes": "SELECT count(*) FROM (SELECT code FROM subjects WHERE code IS NOT NULL GROUP BY code HAVING count(DISTINCT name)>1) c",
        }.items():
            print(f"{label}={db.execute(text(sql)).scalar()}")


if __name__ == "__main__":
    main()
