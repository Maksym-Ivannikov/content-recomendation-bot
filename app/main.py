import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable

from app.config import settings, resolve_admin_ids
from app.db import init_db, async_session
from app.handlers import common, recommendations, quizzes_create, quizzes_run, admin, leaders
from app.scheduler import setup_scheduler


# 👇 Middleware, що зрізає @botname у командах ДО розпізнавання фільтрами
class StripBotnameMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[types.Update, Dict[str, Any]], Awaitable[Any]],
        event: types.Update,
        data: Dict[str, Any]
    ) -> Any:
        message = event.message
        if message and message.text and message.text.startswith("/") and "@" in message.text:
            clean_text = message.text.split("@")[0]
            new_message = message.model_copy(update={"text": clean_text})
            new_event = event.model_copy(update={"message": new_message})
            return await handler(new_event, data)
        return await handler(event, data)


async def main():
    if not settings.BOT_TOKEN or not settings.DATABASE_URL or not settings.GROUP_CHAT_ID:
        raise RuntimeError("Заповни BOT_TOKEN, POSTGRES_URL, GROUP_CHAT_ID у .env")

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    await init_db()
    await resolve_admin_ids(bot)

    bot.db = await async_session().__aenter__()
    await common.set_bot_commands(bot)
    setup_scheduler(bot)

    # ✅ реєструємо всі роутери
    dp.include_router(common.router)
    dp.include_router(recommendations.router)
    dp.include_router(quizzes_create.router)
    dp.include_router(quizzes_run.router)
    dp.include_router(admin.router)
    dp.include_router(leaders.router)

    # ✅ middleware тепер на рівні update (працює до CommandFilter)
    dp.update.middleware(StripBotnameMiddleware())

    print("✅ Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
