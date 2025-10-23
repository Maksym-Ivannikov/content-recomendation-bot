from aiogram import Router, F
from aiogram.types import Message, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, BotCommandScopeChat
from app.config import settings
from app.repositories import upsert_user

router = Router()


@router.message(F.text.regexp(r"^/(start|about)(@.+)?$"))
async def cmd_start(message: Message):
    await upsert_user(message.bot.db, message.from_user.id, message.from_user.username, message.from_user.first_name)
    text = (
        "🤖 Бот рекомендацій і квізів\n\n"
        "📖 Ділись улюбленими книгами, фільмами, серіалами чи іграми.\n"
        "🧠 Проходь квізи у приваті.\n"
        "🏆 Змагайся у лідерах.\n"
    )
    await message.answer(text)


async def set_bot_commands(bot):
    # --- Команди для груп ---
    await bot.set_my_commands([
        BotCommand(command="create_rec", description="📖 Створити рекомендацію"),
        BotCommand(command="get_recs",   description="📚 Переглянути рекомендації"),
        BotCommand(command="quiz",       description="🧠 Пройти квіз"),
        BotCommand(command="leaders",    description="🏆 Лідери квізів"),
        BotCommand(command="about",      description="ℹ️ Про бота"),
    ], scope=BotCommandScopeAllGroupChats())

    # --- Базові команди для всіх у приваті ---
    base_private_cmds = [
        BotCommand(command="create_rec",  description="📖 Створити рекомендацію"),
        BotCommand(command="create_quiz", description="🧠 Створити квіз"),
        BotCommand(command="quiz",        description="🧠 Пройти квіз"),
        BotCommand(command="my_results",  description="📊 Мої результати"),
        BotCommand(command="about",       description="ℹ️ Про бота"),
    ]
    await bot.set_my_commands(base_private_cmds, scope=BotCommandScopeAllPrivateChats())

       # --- Команди для адмінів (додаємо поверх базових) ---
    admin_cmds = base_private_cmds + [
        BotCommand(command="pending", description="🕓 Очікують схвалення"),
    ]

    for admin_id in settings.ADMIN_IDS:
        await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=admin_id))

# --- Вітання нових користувачів у групі ---
from aiogram.types import ChatMemberUpdated

@router.chat_member()
async def greet_new_member(event: ChatMemberUpdated):
    """
    Автоматичне вітання нових користувачів у групі.
    """
    # Перевіряємо, чи це новий учасник
    if event.new_chat_member.status == "member" and event.chat.type in ("group", "supergroup"):
        new_user = event.new_chat_member.user
        # Якщо новий користувач — не бот
        if not new_user.is_bot:
            await event.bot.send_message(
                event.chat.id,
                f"👋 Привіт, {new_user.first_name}!\n"
                f"Щоб користуватися ботом повністю — натисни кнопку Start у приваті 👇\n"
                f"👉 [@{(await event.bot.me()).username}](https://t.me/{(await event.bot.me()).username})",
                disable_web_page_preview=True
            )
