# WhatsApp Message Automation Platform

A modular Python automation system designed to persist recipient contacts, assign customized message templates with dynamic variable interpolation (`{name}`), and dispatch messages via official API providers.

---

## Technical Stack & Architecture

- **Python**: 3.11+
- **Database**: SQLite 3 (with foreign key enforcement and cascade deletes)
- **Validation**: Google `phonenumbers` engine for E.164 international standardization
- **Environment Management**: `python-dotenv` for configuration separation

### Folder Architecture

```text
whatsapp_automation/
│
├── config.py           # Environment variables & configuration validator
├── database.py         # SQLite database connection manager & schema migrations
├── models.py           # Data domain models (Recipient, Message, MessageLog)
├── recipients.py       # Persistence layer & service repository (CRUD + Templating)
├── validation.py       # E.164 phone & input validators
├── requirements.txt    # Project dependencies
├── .env.example        # Environment variable blueprint
└── .gitignore          # Version control exclusion rules