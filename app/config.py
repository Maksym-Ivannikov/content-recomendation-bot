import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv("POSTGRES_URL", "")
    GROUP_CHAT_ID: str = os.getenv("GROUP_CHAT_ID", "")

    # Список юзернеймів адмінів (через кому)
    ADMIN_USERNAMES: list[str] = field(
        default_factory=lambda: [
            u.strip().lstrip("@")
            for u in os.getenv("ADMIN_USERNAMES", "").split(",")
            if u.strip()
        ]
    )

    # ✅ Тепер читає числові ID адмінів напряму з .env
    ADMIN_IDS: list[int] = field(
        default_factory=lambda: [
            int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
        ]
    )

    TZ: str = os.getenv("TIMEZONE", "Europe/Bucharest")


settings = Settings()


async def resolve_admin_ids(bot):
    """Підтягнути або оновити ID адмінів."""
    # Якщо вже явно задано ADMIN_IDS — пропускаємо пошук
    if getattr(settings, "ADMIN_IDS", []):
        print(f"✅ Адміни (IDs): {settings.ADMIN_IDS}")
        return

    resolved_ids = []
    for username in settings.ADMIN_USERNAMES:
        try:
            user = await bot.get_chat(username)
            resolved_ids.append(user.id)
        except Exception as e:
            print(f"⚠️ Не вдалося знайти @{username}: {e}")

    settings.ADMIN_IDS = resolved_ids
    print(f"✅ Адміни (IDs): {settings.ADMIN_IDS}")
