from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
from app.config import settings
from app.db import async_session
from app.repositories import weekly_recommendations

def setup_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=timezone(settings.TZ))

    async def weekly_digest():
        async with async_session() as db:
            recs = await weekly_recommendations(db)
        if not recs:
            return
        text = ["🗓 Рекомендації цього тижня:\n"]
        for r in recs:
            emoji = {"movie":"🎬","series":"📺","book":"📖","game":"🎮"}.get(r.type, "⭐")
            author = f"@{r.username}" if r.username else "користувач"
            text.append(f"{emoji} {r.title}\n👤 {author}\n💬 {r.description}\n")
        msg = "\n".join(text).strip()
        try:
            await bot.send_message(settings.GROUP_CHAT_ID, msg)
        except Exception as e:
            print(f"⚠️ Не вдалося надіслати дайджест: {e}")

    # П’ятниця 20:00 за Europe/Bucharest
    scheduler.add_job(weekly_digest, "cron", day_of_week="fri", hour=20, minute=0)
    scheduler.start()
    return scheduler
