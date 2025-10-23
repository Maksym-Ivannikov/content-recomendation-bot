from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.config import settings
from app.db import async_session
from app.repositories import get_pending_questions, approve_question
from app.keyboards import approve_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.ADMIN_IDS


# --- показати питання, що очікують на модерацію
@router.message(F.text.in_({"/pending", "/pending_questions"}))
async def pending_questions(message: Message):
    if not is_admin(message.from_user.id):
        return

    async with async_session() as db:
        items = await get_pending_questions(db, limit=1)

    if not items:
        await message.answer("✅ Немає питань на модерацію.")
        return

    q = items[0]
    text = (
        f"📝 Питання #{q.id} (квіз {q.quiz_id})\n\n"
        f"{q.text}\n"
        f"А) {q.option_a}\n"
        f"Б) {q.option_b}\n"
        f"В) {q.option_c}\n\n"
        f"Правильна: {q.correct_option}\n"
        f"Автор: {q.created_by}"
    )
    await message.answer(text, reply_markup=approve_kb(q.id))


# --- обробка кнопок "Схвалити / Відхилити"
@router.callback_query(F.data.startswith("admin:approve:"))
async def admin_approve(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("Тільки для адмінів.", show_alert=True)
        return

    _, _, qid, val = cb.data.split(":")
    async with async_session() as db:
        await approve_question(db, int(qid), approve=(val == "1"))

    await cb.message.edit_text("✅ Збережено. Використай /pending щоб продовжити.")
    await cb.answer()


# --- обробка кнопки "Далі"
@router.callback_query(F.data == "admin:next")
async def admin_next(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("Тільки для адмінів.", show_alert=True)
        return

    await cb.message.edit_text("➡️ Використай /pending щоб показати наступне питання.")
    await cb.answer()
