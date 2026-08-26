"""
Terminal-based User Interface (CLI) for WhatsApp Automation.
Handles user interaction, recipient CRUD workflows, message composition,
pre-send previews, dispatch displays, and retry management.
"""

import os
import sys
from typing import List, Optional, Tuple

from config import config
from models import DeliveryStatus, Recipient
from recipients import MessageRepository, RecipientRepository
from messaging import MessagingEngine, MessageLogRepository
from validation import (
    ValidationError,
    validate_message_text,
    validate_phone_number,
    validate_positive_integer,
)


class TerminalUI:
    """Manages terminal interactions and interactive menus."""

    def __init__(self):
        self.recipient_repo = RecipientRepository()
        self.message_repo = MessageRepository()
        self.log_repo = MessageLogRepository()

    @staticmethod
    def clear_screen() -> None:
        """Clears the terminal screen for better visual clarity."""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def print_header(title: str) -> None:
        """Renders a standardized header box."""
        print("\n" + "=" * 50)
        print(f"  {title.upper()}")
        print("=" * 50)

    # =========================================================================
    # Menu Flow & Navigation
    # =========================================================================

    def run_main_menu(self) -> None:
        """Main application loop."""
        while True:
            self.print_header("WhatsApp Message Automation")
            print("1. Add recipients")
            print("2. View recipients")
            print("3. Edit recipient")
            print("4. Delete recipient")
            print("5. Create / Edit messages")
            print("6. Send messages")
            print("7. View sending history & Retry failed")
            print("8. Clear all saved data")
            print("9. Exit")
            print("=" * 50)

            choice = input("Select option (1-9): ").strip()

            if choice == "1":
                self.add_recipients_flow()
            elif choice == "2":
                self.view_recipients_flow()
            elif choice == "3":
                self.edit_recipient_flow()
            elif choice == "4":
                self.delete_recipient_flow()
            elif choice == "5":
                self.create_messages_menu()
            elif choice == "6":
                self.send_messages_flow()
            elif choice == "7":
                self.view_history_and_retry_flow()
            elif choice == "8":
                self.clear_all_data_flow()
            elif choice == "9":
                print("\nExiting application. Goodbye!")
                sys.exit(0)
            else:
                input("\nInvalid option. Press [Enter] to try again...")

    # =========================================================================
    # Recipient Management Workflows
    # =========================================================================

    def add_recipients_flow(self) -> None:
        """Adds a user-defined count of recipients sequentially."""
        self.print_header("Add Recipients")

        try:
            count_str = input("How many people do you want to add? ").strip()
            count = validate_positive_integer(count_str)
        except ValidationError as err:
            print(f"\n[Error]: {err}")
            input("\nPress [Enter] to return to the main menu...")
            return

        added_count = 0
        for idx in range(1, count + 1):
            print(f"\n--- Person {idx} of {count} ---")

            while True:
                name = input("Name: ").strip()
                if not name:
                    print("  [Validation Error]: Name cannot be empty.")
                    continue
                break

            while True:
                phone = input("WhatsApp Number (e.g. +919876543210): ").strip()
                try:
                    formatted_phone = validate_phone_number(phone)
                    self.recipient_repo.add_recipient(name, formatted_phone)
                    print(f"  ✓ Saved: {name} ({formatted_phone})")
                    added_count += 1
                    break
                except ValidationError as err:
                    print(f"  [Validation Error]: {err}")
                    retry_choice = input("  Try again for this person? (Y/N): ").strip().lower()
                    if retry_choice != "y":
                        print("  Skipping this entry.")
                        break

        print(f"\nFinished adding {added_count} recipient(s).")
        input("\nPress [Enter] to return to the main menu...")

    def view_recipients_flow(self) -> None:
        """Displays all saved recipients along with their assigned messages."""
        self.print_header("Saved Recipients")
        pairs = self.message_repo.get_all_recipient_message_pairs()

        if not pairs:
            print("No recipients found in database.")
        else:
            print(f"{'ID':<4} | {'Name':<15} | {'Phone Number':<16} | {'Assigned Message'}")
            print("-" * 75)
            for recipient, message_text in pairs:
                msg_preview = (
                    (message_text[:25] + "...") if message_text and len(message_text) > 25 else (message_text or "[No message set]")
                )
                print(
                    f"{recipient.id:<4} | {recipient.name:<15} | {recipient.phone_number:<16} | {msg_preview}"
                )

        input("\nPress [Enter] to return to main menu...")

    def edit_recipient_flow(self) -> None:
        """Edits an existing recipient's name or phone number."""
        self.print_header("Edit Recipient")
        recipients = self.recipient_repo.get_all_recipients()

        if not recipients:
            print("No recipients available to edit.")
            input("\nPress [Enter] to return...")
            return

        for r in recipients:
            print(f"[{r.id}] {r.name} - {r.phone_number}")

        rec_id_str = input("\nEnter Recipient ID to edit: ").strip()
        try:
            rec_id = int(rec_id_str)
            target = self.recipient_repo.get_recipient_by_id(rec_id)
            if not target:
                raise ValidationError(f"No recipient found with ID {rec_id}.")
        except ValueError:
            print("\n[Error]: ID must be a numeric integer.")
            input("\nPress [Enter] to return...")
            return
        except ValidationError as err:
            print(f"\n[Error]: {err}")
            input("\nPress [Enter] to return...")
            return

        print(f"\nEditing target: {target.name} ({target.phone_number})")
        new_name = input(f"New Name [{target.name}]: ").strip() or target.name
        new_phone_raw = input(f"New Phone [{target.phone_number}]: ").strip() or target.phone_number

        try:
            updated = self.recipient_repo.update_recipient(rec_id, new_name, new_phone_raw)
            print(f"\n✓ Successfully updated to: {updated.name} ({updated.phone_number})")
        except ValidationError as err:
            print(f"\n[Error]: {err}")

        input("\nPress [Enter] to return...")

    def delete_recipient_flow(self) -> None:
        """Removes a single recipient and their message records."""
        self.print_header("Delete Recipient")
        recipients = self.recipient_repo.get_all_recipients()

        if not recipients:
            print("No recipients available to delete.")
            input("\nPress [Enter] to return...")
            return

        for r in recipients:
            print(f"[{r.id}] {r.name} - {r.phone_number}")

        rec_id_str = input("\nEnter Recipient ID to delete: ").strip()
        try:
            rec_id = int(rec_id_str)
            if self.recipient_repo.delete_recipient(rec_id):
                print(f"\n✓ Recipient ID {rec_id} deleted successfully.")
            else:
                print(f"\n[Error]: Recipient ID {rec_id} not found.")
        except ValueError:
            print("\n[Error]: ID must be a numeric integer.")

        input("\nPress [Enter] to return...")

    def clear_all_data_flow(self) -> None:
        """Clears all recipients and message tables after explicit confirmation."""
        self.print_header("Clear All Saved Data")
        confirm = input("Are you SURE you want to delete ALL recipients and messages? [y/N]: ").strip().lower()
        if confirm == "y":
            self.recipient_repo.clear_all_recipients()
            print("\n✓ Database cleared successfully.")
        else:
            print("\nOperation cancelled.")
        input("\nPress [Enter] to return...")

    # =========================================================================
    # Customized Message Workflows
    # =========================================================================

    def create_messages_menu(self) -> None:
        """Presents options to configure custom messages."""
        while True:
            self.print_header("Create / Edit Customized Messages")
            print("1. Create/Edit message for a single recipient")
            print("2. Create/Edit messages for ALL recipients sequentially")
            print("3. Return to main menu")
            print("-" * 50)
            print("Tip: Use '{name}' inside templates for dynamic substitution.")
            print("Example: 'Hi {name}, please complete your task.'")
            print("-" * 50)

            choice = input("Select option (1-3): ").strip()

            if choice == "1":
                self.single_message_flow()
            elif choice == "2":
                self.bulk_message_flow()
            elif choice == "3":
                break

    def single_message_flow(self) -> None:
        """Assigns a custom message to a selected recipient."""
        recipients = self.recipient_repo.get_all_recipients()
        if not recipients:
            print("\nNo recipients found. Please add recipients first.")
            input("\nPress [Enter] to return...")
            return

        print("\nSelect recipient:")
        for r in recipients:
            msg = self.message_repo.get_message_for_recipient(r.id)
            status_str = f"Current message: '{msg.message_text}'" if msg else "No message configured"
            print(f"[{r.id}] {r.name} - {r.phone_number} ({status_str})")

        rec_id_str = input("\nEnter recipient ID: ").strip()
        try:
            rec_id = int(rec_id_str)
            target = self.recipient_repo.get_recipient_by_id(rec_id)
            if not target:
                print(f"\n[Error]: Recipient ID {rec_id} not found.")
                input("\nPress [Enter] to return...")
                return

            print(f"\nEnter customized message for {target.name}:")
            msg_input = input("> ").strip()
            
            self.message_repo.save_or_update_message(rec_id, msg_input)
            
            # Show preview with template rendering
            rendered = MessageRepository.render_personalized_message(msg_input, target)
            print(f"\n✓ Saved! Preview for {target.name}:")
            print(f"  \"{rendered}\"")

        except ValueError:
            print("\n[Error]: Invalid ID integer.")
        except ValidationError as err:
            print(f"\n[Validation Error]: {err}")

        input("\nPress [Enter] to return...")

    def bulk_message_flow(self) -> None:
        """Loops through every recipient to define custom messages sequentially."""
        recipients = self.recipient_repo.get_all_recipients()
        if not recipients:
            print("\nNo recipients found. Please add recipients first.")
            input("\nPress [Enter] to return...")
            return

        print("\n=== Loop Mode: Define Messages for All Recipients ===")
        print("Press [Enter] without typing to leave an existing message unchanged.\n")

        for r in recipients:
            existing = self.message_repo.get_message_for_recipient(r.id)
            prompt_str = f"Message for {r.name} ({r.phone_number})"
            if existing:
                prompt_str += f" [Current: '{existing.message_text}']"
            print(f"{prompt_str}:")

            msg_input = input("> ").strip()

            if not msg_input and existing:
                print("  Keeping existing message.\n")
                continue
            elif not msg_input and not existing:
                print("  Skipped (No message set).\n")
                continue

            try:
                self.message_repo.save_or_update_message(r.id, msg_input)
                rendered = MessageRepository.render_personalized_message(msg_input, r)
                print(f"  ✓ Saved! Rendered: \"{rendered}\"\n")
            except ValidationError as err:
                print(f"  [Validation Error]: {err}. Skipping.\n")

        input("Finished configuring messages. Press [Enter] to return...")

    # =========================================================================
    # Sending & Confirmation Workflow
    # =========================================================================

    def send_messages_flow(self) -> None:
        """Reviews messages, prompts confirmation, and triggers dispatch."""
        self.print_header("Send Messages - Confirmation")

        pairs = self.message_repo.get_all_recipient_message_pairs()
        valid_send_items: List[Tuple[Recipient, str]] = []

        if not pairs:
            print("No recipients stored. Please add recipients first.")
            input("\nPress [Enter] to return...")
            return

        print("=== Final Dispatch Preview ===\n")
        skipped_count = 0

        for recipient, raw_message in pairs:
            if not raw_message or not raw_message.strip():
                print(f"Recipient: {recipient.name}")
                print(f"Number:    {recipient.phone_number}")
                print("Message:   [SKIPPED - No message configured]\n")
                skipped_count += 1
            else:
                rendered_msg = MessageRepository.render_personalized_message(raw_message, recipient)
                print(f"Recipient: {recipient.name}")
                print(f"Number:    {recipient.phone_number}")
                print(f"Message:   {rendered_msg}\n")
                valid_send_items.append((recipient, raw_message))

        if not valid_send_items:
            print("No valid recipients with assigned messages ready to send.")
            input("\nPress [Enter] to return...")
            return

        print(f"Total ready to send: {len(valid_send_items)} | Skipped: {skipped_count}")
        confirm = input("\nSend these messages? [Y/N]: ").strip().lower()

        if confirm != "y":
            print("\nSending sequence cancelled by user.")
            input("\nPress [Enter] to return...")
            return

        # Execute Sending Sequence
        print("\nStarting WhatsApp messaging dispatch engine...")
        print("-" * 50)

        try:
            engine = MessagingEngine()
            results = engine.batch_send(valid_send_items)

            # Render Status Summary Table
            self.print_header("Sending Status Summary")
            print(f"{'Name':<15} | {'Phone Number':<16} | {'Status':<10} | {'Details / Message ID'}")
            print("-" * 75)

            for recipient, log in results:
                detail = log.provider_message_id if log.status == DeliveryStatus.SENT else (log.error_message or "N/A")
                print(f"{recipient.name:<15} | {recipient.phone_number:<16} | {log.status.value:<10} | {detail}")

        except ValueError as err:
            print(f"\n[Configuration Error]: {err}")
        except Exception as exc:
            print(f"\n[Unexpected Error during sending]: {exc}")

        input("\nSending process completed. Press [Enter] to return...")

    # =========================================================================
    # History & Retry Workflows
    # =========================================================================

    def view_history_and_retry_flow(self) -> None:
        """Displays audit log history and allows retrying failed messages."""
        self.print_header("Sending History & Retry")

        logs = self.log_repo.get_all_logs()
        if not logs:
            print("No delivery history records found.")
            input("\nPress [Enter] to return...")
            return

        print(f"{'Date/Time':<19} | {'Name':<12} | {'Phone':<15} | {'Status':<8} | {'Error/Provider ID'}")
        print("-" * 80)

        failed_recipients: List[Tuple[Recipient, str]] = []

        for log in logs:
            time_str = str(log["sent_at"])[:19]
            err_or_id = log["provider_message_id"] if log["status"] == "SENT" else (log["error_message"] or "N/A")
            if len(err_or_id) > 20:
                err_or_id = err_or_id[:17] + "..."

            print(f"{time_str:<19} | {log['name']:<12} | {log['phone_number']:<15} | {log['status']:<8} | {err_or_id}")

            if log["status"] == DeliveryStatus.FAILED.value:
                r = Recipient(id=log["recipient_id"], name=log["name"], phone_number=log["phone_number"])
                failed_recipients.append((r, log["message_text"]))

        if failed_recipients:
            print(f"\nFound {len(failed_recipients)} failed message attempt(s).")
            retry_choice = input("Do you want to retry sending failed messages now? [y/N]: ").strip().lower()
            if retry_choice == "y":
                print("\nInitiating retry sequence for failed recipients...")
                engine = MessagingEngine()
                results = engine.batch_send(failed_recipients)

                print("\nRetry Results:")
                for recipient, new_log in results:
                    print(f"  {recipient.name} ({recipient.phone_number}): {new_log.status.value}")

        input("\nPress [Enter] to return...")