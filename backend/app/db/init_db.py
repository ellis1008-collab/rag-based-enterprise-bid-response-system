from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401
from sqlalchemy import inspect, text


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_bid_response_review_columns()


def ensure_bid_response_review_columns() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if "bid_responses" not in table_names:
        return

    existing_columns = {column["name"] for column in inspector.get_columns("bid_responses")}
    dialect_name = engine.dialect.name
    updated_at_type = "TIMESTAMP WITH TIME ZONE" if dialect_name == "postgresql" else "DATETIME"

    statements: list[str] = []
    if "human_status" not in existing_columns:
        statements.append("ALTER TABLE bid_responses ADD COLUMN human_status VARCHAR(50) DEFAULT 'pending'")
    if "human_note" not in existing_columns:
        statements.append("ALTER TABLE bid_responses ADD COLUMN human_note TEXT")
    if "updated_at" not in existing_columns:
        statements.append(f"ALTER TABLE bid_responses ADD COLUMN updated_at {updated_at_type}")

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))

        connection.execute(
            text("UPDATE bid_responses SET human_status = 'pending' WHERE human_status IS NULL OR human_status = ''")
        )
        connection.execute(text("UPDATE bid_responses SET human_note = '' WHERE human_note IS NULL"))
        connection.execute(text("UPDATE bid_responses SET updated_at = created_at WHERE updated_at IS NULL"))
