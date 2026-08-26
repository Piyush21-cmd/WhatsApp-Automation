"""
Integration tests for database CRUD, recipient management, and message personalization.
"""

from pathlib import Path
import pytest
from database import DatabaseManager
from models import Recipient
from recipients import MessageRepository, RecipientRepository
from validation import ValidationError


@pytest.fixture
def test_db(tmp_path: Path, monkeypatch):
    """Sets up a temporary SQLite database file for testing."""
    test_db_path = tmp_path / "test_recipients.db"
    
    # Patch the config database path
    from config import config
    monkeypatch.setattr(config, "DATABASE_PATH", test_db_path)
    
    db_mgr = DatabaseManager(db_path=test_db_path)
    db_mgr.initialize_schema()
    
    # Patch database manager reference in modules
    monkeypatch.setattr("recipients.db", db_mgr)

    return db_mgr


def test_recipient_crud_and_duplicates(test_db):
    repo = RecipientRepository()

    # Add recipient
    rec1 = repo.add_recipient("Rahul", "+919876543210")
    assert rec1.id is not None
    assert rec1.phone_number == "+919876543210"

    # Reject duplicate phone number
    with pytest.raises(ValidationError):
        repo.add_recipient("Rahul Duplicate", "+919876543210")

    # Fetch all
    all_recs = repo.get_all_recipients()
    assert len(all_recs) == 1

    # Update recipient
    updated = repo.update_recipient(rec1.id, "Rahul Sharma", "+919876543210")
    assert updated.name == "Rahul Sharma"

    # Delete recipient
    deleted = repo.delete_recipient(rec1.id)
    assert deleted is True
    assert len(repo.get_all_recipients()) == 0


def test_message_upsert_and_templating(test_db):
    rec_repo = RecipientRepository()
    msg_repo = MessageRepository()

    rec = rec_repo.add_recipient("Amit", "+919876543211")

    # Save custom message
    raw_msg = "Hello {name}, please submit report."
    saved_msg = msg_repo.save_or_update_message(rec.id, raw_msg)
    assert saved_msg.message_text == raw_msg

    # Upsert (Update existing)
    updated_msg = msg_repo.save_or_update_message(rec.id, "Hi {name}, report is due.")
    assert updated_msg.message_text == "Hi {name}, report is due."

    # Test dynamic personalization
    rendered = MessageRepository.render_personalized_message(updated_msg.message_text, rec)
    assert rendered == "Hi Amit, report is due."