# Alembic Directory

This directory contains all database migration scripts and configuration for managing relational database schema using Alembic and SQLAlchemy.

- `env.py`: Alembic environment configuration, loads SQLAlchemy models for autogeneration.
- `versions/`: Contains migration scripts (e.g., `0001_create_document_metadata.py`).
- `alembic.ini`: Main Alembic configuration file (in project root).

## Usage

1. **Configure your database URL** in `alembic.ini` (default is SQLite, can be Postgres, etc.).
2. **Run migrations:**
   ```bash
   alembic upgrade head
   ```
3. **Create new migrations after model changes:**
   ```bash
   alembic revision --autogenerate -m "describe your change"
   alembic upgrade head
   ```

See the main README for more details on when migrations are required. 