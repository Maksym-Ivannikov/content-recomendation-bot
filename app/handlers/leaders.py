from aiogram import Router, F
from aiogram.types import Message
from app.db import async_session
from app.repositories import top3_by_category, user_results

router = Router()


# 🏆 Груповий рейтинг — доступний у групах
@router.message(F.text == "/leaders")
async def leaders(message: Message):
    async with async_session() as db:
        cats = [("📖 Книги", "book"), ("🎬 Фільми", "movie"), ("📺 Серіали", "series"), ("🎮 Ігри", "game")]
        lines = ["🏆 Топ-3 за категоріями:\n"]
        for emoji_name, cat in cats:
            rows = await top3_by_category(db, cat)
            if not rows:
                lines.append(f"{emoji_name} — немає результатів\n")
                continue
            lines.append(f"{emoji_name}:")
            for i, r in enumerate(rows, start=1):
                pct = int(round(100 * (r['pct'] or 0)))
                uname = f"@{r['username']}" if r['username'] else f"id:{r['user_id']}"
                lines.append(f"{i}️⃣ {uname} — {pct}%")
            lines.append("")  # порожній рядок
        await message.answer("\n".join(lines).strip())


# 📊 Персональні результати — доступні в приваті
@router.message(F.text == "/my_results")
async def my_results(message: Message):
    async with async_session() as db:
        results = await user_results(db, message.from_user.id)

    if not results:
        await message.answer("📉 Ти ще не проходив жодного квізу.")
        return

    # емоджі за типом
    emoji_map = {"movie": "🎬", "series": "📺", "book": "📚", "game": "🎮"}

    lines = ["📊 Твої результати:\n"]
    for r in results:
        pct = int(round(r["pct"]))  
        # дізнаємось тип квізу, щоб підібрати емоджі
        cat_emoji = emoji_map.get(r.get("type"), "💡")
        lines.append(f"{cat_emoji} {r['title']} — {pct}%")

    await message.answer("\n".join(lines))
