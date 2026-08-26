# WhatsApp Message Automation Platform

A production-grade Python CLI application designed to save a configurable list of WhatsApp recipients, map custom personalized messages to each recipient, and dispatch them via Meta's official WhatsApp Cloud API.

---

## Key Features

- **Persistent Contact Management**: Saves recipients and custom messages locally using SQLite 3 with foreign key cascades.
- **International Phone Validation**: Parses and standardizes phone numbers into international E.164 format (`+919876543210`) using Google's `phonenumbers` engine.
- **Dynamic Personalization**: Assign unique messages per recipient or use dynamic placeholders like `{name}` (e.g., `"Hi {name}, please submit your report."` converts to `"Hi Rahul, please submit your report."`).
- **Official Meta Cloud API Engine**: Uses Meta's Graph API instead of browser scraping or unauthorized automation tools.
- **Resilient Delivery & Retries**: Includes configurable rate limiting, exponential backoff retries, error capturing, and targeted retry workflows for failed messages.
- **Audit History**: Complete logging of recipient ID, phone number, delivery status (`SENT`, `FAILED`, `SKIPPED`), provider message IDs, and error descriptions.

---

## Directory Architecture

```text
whatsapp_automation/
│
├── app.py              # Application entry point & pre-flight setup
├── config.py           # Environment configuration parser
├── database.py         # SQLite connection manager & migrations
├── models.py           # Domain models & delivery enums
├── recipients.py       # Persistence layer & templating engine
├── messaging.py        # Meta Cloud API client, rate limiter & retry engine
├── validation.py       # E.164 phone & input validators
├── ui.py               # Interactive CLI terminal screens
├── requirements.txt    # Project dependencies
├── .env.example        # Environment blueprint template
├── README.md           # Documentation & operational guide
└── tests/
    ├── test_validation.py
    ├── test_recipients.py
    └── test_messaging.py