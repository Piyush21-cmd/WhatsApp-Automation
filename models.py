"""
Data transfer objects and domain models for the WhatsApp Automation system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

#kya possible ways ho sakete h messages ke 
#random strings jaise ki  'success' or 'done' ko bina flow ke na use kare 
class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
#ye dikhata h wo ek insan jise message bhejna ho 
class Recipient:
    id: Optional[int]
    name: str
    phone_number: str  # Stored strictly in E.164 format
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
#the actull customer message to a recipient(The actull Message Text)
class Message:
    id: Optional[int]
    recipient_id: int
    message_text: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass

class MessageLog:
    id: Optional[int]
    recipient_id: int
    message_text: str
    status: DeliveryStatus
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None