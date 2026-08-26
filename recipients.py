"""
Service layer for recipient and custom message management.
"""

import sqlite3
from typing import List, Optional, Tuple
from database import db
from models import Message, Recipient
from validation import ValidationError, validate_message_text, validate_phone_number


class RecipientRepository:
    """Manages CRUD operations for Recipients and customized Messages."""

    def add_recipient(self, name: str, phone_number: str) -> Recipient:
        """
        Validates input and saves a new recipient to the database.
        Prevents duplicate phone numbers.
        """
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("Recipient name cannot be empty.")

        formatted_phone = validate_phone_number(phone_number)

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Check for existing duplicate number
            cursor.execute(
                "SELECT id FROM recipients WHERE phone_number = ?",
                (formatted_phone,),
            )
            if cursor.fetchone():
                raise ValidationError(
                    f"Phone number '{formatted_phone}' already exists in the database."
                )

            cursor.execute(
                "INSERT INTO recipients (name, phone_number) VALUES (?, ?)",
                (clean_name, formatted_phone),
            )
            recipient_id = cursor.lastrowid

            return Recipient(
                id=recipient_id,
                name=clean_name,
                phone_number=formatted_phone,
            )

    def get_recipient_by_id(self, recipient_id: int) -> Optional[Recipient]:
        """Retrieves a single recipient by primary key."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, phone_number, created_at, updated_at FROM recipients WHERE id = ?",
                (recipient_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Recipient(
                id=row["id"],
                name=row["name"],
                phone_number=row["phone_number"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def get_all_recipients(self) -> List[Recipient]:
        """Retrieves all stored recipients ordered by ID."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name, phone_number, created_at, updated_at FROM recipients ORDER BY id ASC"
            )
            rows = cursor.fetchall()
            return [
                Recipient(
                    id=row["id"],
                    name=row["name"],
                    phone_number=row["phone_number"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def update_recipient(self, recipient_id: int, name: str, phone_number: str) -> Recipient:
        """Updates an existing recipient's details."""
        clean_name = name.strip()
        if not clean_name:
            raise ValidationError("Recipient name cannot be empty.")

        formatted_phone = validate_phone_number(phone_number)

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Check if another record already uses this updated phone number
            cursor.execute(
                "SELECT id FROM recipients WHERE phone_number = ? AND id != ?",
                (formatted_phone, recipient_id),
            )
            if cursor.fetchone():
                raise ValidationError(
                    f"Phone number '{formatted_phone}' belongs to another recipient."
                )

            cursor.execute(
                """
                UPDATE recipients
                SET name = ?, phone_number = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (clean_name, formatted_phone, recipient_id),
            )

            if cursor.rowcount == 0:
                raise ValidationError(f"Recipient with ID {recipient_id} does not exist.")

            return Recipient(id=recipient_id, name=clean_name, phone_number=formatted_phone)

    def delete_recipient(self, recipient_id: int) -> bool:
        """Deletes a recipient and cascades to their messages."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipients WHERE id = ?", (recipient_id,))
            return cursor.rowcount > 0

    def clear_all_recipients(self) -> None:
        """Clears all recipients, associated messages, and log records."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM message_logs")
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM recipients")


class MessageRepository:
    """Manages mapping between Recipients and customized messages."""

    def save_or_update_message(self, recipient_id: int, message_text: str) -> Message:
        """
        Saves or updates a custom message for a recipient (UPSERT).
        """
        clean_text = validate_message_text(message_text)

        with db.get_connection() as conn:
            cursor = conn.cursor()

            # Verify recipient exists
            cursor.execute("SELECT id FROM recipients WHERE id = ?", (recipient_id,))
            if not cursor.fetchone():
                raise ValidationError(f"Recipient ID {recipient_id} not found.")

            # Perform UPSERT SQLite syntax
            cursor.execute(
                """
                INSERT INTO messages (recipient_id, message_text)
                VALUES (?, ?)
                ON CONFLICT(recipient_id) DO UPDATE SET
                    message_text = excluded.message_text,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (recipient_id, clean_text),
            )

            cursor.execute(
                "SELECT id, recipient_id, message_text, created_at, updated_at FROM messages WHERE recipient_id = ?",
                (recipient_id,),
            )
            row = cursor.fetchone()
            return Message(
                id=row["id"],
                recipient_id=row["recipient_id"],
                message_text=row["message_text"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def get_message_for_recipient(self, recipient_id: int) -> Optional[Message]:
        """Gets the configured message for a specific recipient."""
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, recipient_id, message_text, created_at, updated_at FROM messages WHERE recipient_id = ?",
                (recipient_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return Message(
                id=row["id"],
                recipient_id=row["recipient_id"],
                message_text=row["message_text"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def get_all_recipient_message_pairs(self) -> List[Tuple[Recipient, Optional[str]]]:
        """
        Retrieves all recipients with their assigned message (if any).
        Returns list of (Recipient, message_text_or_None) tuples.
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    r.id as r_id, r.name, r.phone_number, r.created_at as r_created, r.updated_at as r_updated,
                    m.message_text
                FROM recipients r
                LEFT JOIN messages m ON r.id = m.recipient_id
                ORDER BY r.id ASC
                """
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                recipient = Recipient(
                    id=row["r_id"],
                    name=row["name"],
                    phone_number=row["phone_number"],
                    created_at=row["r_created"],
                    updated_at=row["r_updated"],
                )
                results.append((recipient, row["message_text"]))
            return results

    @staticmethod
    def render_personalized_message(raw_template: str, recipient: Recipient) -> str:
        """
        Parses dynamic variables like '{name}' inside message templates.
        Example: "Hi {name},..." -> "Hi Rahul,..."
        """
        if not raw_template:
            return ""

        # Handles {name} replacement smoothly
        rendered = raw_template.replace("{name}", recipient.name)
        return rendered