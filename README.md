# TG Recs & Quizzes Bot

- aiogram 3.x
- PostgreSQL (async SQLAlchemy + asyncpg)
- APScheduler (щоп’ятниці 20:00 Europe/Bucharest — дайджест нових рекомендацій, якщо є)

## .env
BOT_TOKEN=...
POSTGRES_URL=postgresql+asyncpg://user:pass@host:5432/dbname
GROUP_CHAT_ID=-1001234567890
ADMIN_USERNAMES=maximivannikov,sofia_writer
TIMEZONE=Europe/Bucharest

## Run
pip install -r requirements.txt
python -m app.main

## Import one quiz from JSON
python scripts/import_quizzes.py path/to/quiz.json
