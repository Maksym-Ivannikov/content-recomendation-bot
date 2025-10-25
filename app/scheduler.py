from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from app.config import settings
from app.db import async_session
from app.repositories import weekly_recommendations


def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=timezone(settings.TZ))

    async def weekly_digest():
        async with async_session() as db:
            recs = await weekly_recommendations(db)

        if not recs:
            print("ℹ️ Немає нових рекомендацій цього тижня.")
            return

        text = ["🗓 Рекомендації цього тижня:\n"]
        for r in recs:
            emoji = {"movie":"🎬","series":"📺","book":"📖","game":"🎮"}.get(r.type, "⭐")
            author = f"@{r.username}" if r.username else "користувач"
            text.append(f"{emoji} {r.title}\n👤 {author}\n💬 {r.description}\n")
        msg = "\n".join(text).strip()

        # --- створюємо новий екземпляр бота ---
        local_bot = Bot(token=settings.BOT_TOKEN)

        try:
            await local_bot.send_message(settings.GROUP_CHAT_ID, msg)
            print("✅ Дайджест успішно надіслано.")
        except TelegramBadRequest as e:
            print(f"⚠️ Telegram помилка: {e}")
        except Exception as e:
            print(f"⚠️ Не вдалося надіслати дайджест: {e}")
        finally:
            await local_bot.session.close()

    # Запускаємо по п’ятницях о 20:00 (Europe/Bucharest)
    scheduler.add_job(weekly_digest, "cron", day_of_week="sat", hour=13, minute=00)
    scheduler.start()
    return scheduler
