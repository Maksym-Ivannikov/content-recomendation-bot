"""
Імпорт одного квізу з JSON:

python scripts/import_quizzes.py path/to/quiz.json
"""

import json
import sys
import os
import asyncio

# ✅ додаємо корінь проекту у sys.path, щоб імпорти app/... працювали
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.config import settings
from app.db import async_session, init_db
from app.repositories import create_quiz, add_question


async def run(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title = data["title"].strip()
    type_ = data["type"].strip()  # "movie|series|book|game"
    description = data.get("description", None)

    await init_db()
    async with async_session() as db:
        quiz = await create_quiz(db, title, type_, description, created_by=None)
        for q in data.get("questions", []):
            opts = q["options"]
            await add_question(
                db,
                quiz_id=quiz.id,
                text_=q["text"].strip(),
                a=opts[0].strip(),
                b=opts[1].strip(),
                c=opts[2].strip(),
                correct=q["correct"].strip().upper(),
                created_by=None,
                is_approved=True  # ІМПОРТ — одразу верифіковано
            )
    print(f"✅ Імпортовано квіз: {title} (id={quiz.id})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_quizzes.py file.json")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))
