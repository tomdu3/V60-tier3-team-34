# Database Implementation Plan (Supabase)

## Goal
Implement a persistent database using Supabase to store scraped tweets, their generated signals, and user configurations. This ensures data survives between scraping cycles and prevents duplicate processing.

## Sub-Issues Addressed
1. **#36 Create tweets table**: Store tweets and their analysis signals.
2. **#37 Create user_settings table**: Store API keys and configuration.
3. **#38 Configure Supabase client in the backend**: Setup connection and client instantiation.
4. **#39 Add uniqueness constraint to prevent duplicates**: DB-level duplicate prevention.

---

## 1. Database Schema (Supabase SQL)

### Entity Relationship Diagram

```mermaid
erDiagram
    tweets {
        TEXT tweet_timestamp PK "Used as ID since user is always jimcramer"
        TEXT tweet_text
        TEXT tweet_link
        TIMESTAMP created_at
    }
    user_settings {
        UUID id PK
        TEXT email UK "NOT NULL"
        TEXT username UK "NOT NULL"
        TEXT full_name
        TEXT avatar_url
        TEXT password_hash "NOT NULL"
        TIMESTAMP last_login_at
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP deleted_at
    }
```
## 2. Local Database Setup

### Docker Compose
We use Docker Compose to run a local instance of PostgreSQL (Supabase primarily uses Postgres 15+).

**Start the database:**
To start the database in the background:
```bash
docker compose up -d
```

**Stop the database:**
To stop the database container (data remains safe in the volume):
```bash
docker compose down
```

*Note: Database data is persisted in the Docker volume `postgres_data`. If you ever want to completely wipe the local database, you can run `docker compose down -v`.*

## 3. Environment Configuration (`.env`)
Ensure your `server/.env` file contains the database credentials. These are used by both Docker Compose and our application/Alembic to connect.

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=local_password
DATABASE_URL=postgresql+asyncpg://postgres:local_password@localhost:5432/reverse_cramer
```

## 4. Database Migrations (Alembic)

We use Alembic to manage database schema changes based on our SQLAlchemy models located in `server/models/`.

**Configuration Overview:**
- `alembic/env.py` loads the `DATABASE_URL` dynamically from your `.env` file.
- It imports `Base` from `models/__init__.py`, meaning any new models must be exported there to be detected.

**Generating a Migration:**
Whenever you modify, add, or delete a model, you must generate a new migration script. Run this from the `server/` directory:
```bash
uv run alembic revision --autogenerate -m "brief description of changes"
```
This generates a new Python script in `alembic/versions/` containing the required SQL operations.

**Applying Migrations:**
To apply all pending migrations to the local database:
```bash
uv run alembic upgrade head
```

**Rolling Back Migrations:**
If you need to revert the last applied migration:
```bash
uv run alembic downgrade -1
```

## 5. Data Importing & Seeding

### Importing Scraped JSON (`import_tweets.py`)
To process scraped JSON files and insert them into the local database, use the `import_tweets.py` script. It automatically filters the tweets using `filter.py` and safely inserts them into the `tweets` table using an upsert strategy (ignoring duplicates).
```bash
uv run import_tweets.py data/your_scraped_tweets.json
```

### Seeding Mock Data (`seed.py`)
To insert standard mock data into the database (e.g., fake user profiles and sample tweets), use the `seed.py` script. It uses an upsert strategy, so it is safe to run multiple times without causing errors.
```bash
uv run seed.py
```

## 6. Testing & Utilities

### Automated Tests (`test_filter.py` & `conftest.py`)
We use Pytest to automatically verify our application logic.
- `test_filter.py`: Contains the unit tests and integration tests for the tweet filtering logic.
- `conftest.py`: Stores our Pytest fixtures (like raw mock data and SQLAlchemy model instances) which are globally available to all tests.

Run the test suite with:
```bash
uv run pytest
```

### Manual CLI Inspection (`run_filter.py`)
If you want to view how the filter behaves on a specific JSON file *without* inserting anything into the database, use the `run_filter.py` tool. It prints a human-readable summary of the valid tweets directly to your console.
```bash
uv run run_filter.py data/your_scraped_tweets.json
```
