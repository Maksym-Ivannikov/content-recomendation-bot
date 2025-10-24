from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.fsm.states import CreateRec
from app.keyboards import rec_type_kb
from app.config import settings
from app.db import async_session
from app.repositories import add_recommendation, list_recommendations, upsert_user

router = Router()


@router.message(F.text == "/create_rec")
async def create_rec_entry(message: Message, state: FSMContext):
    # Якщо команда з групи — надсилаємо приватне повідомлення
    if message.chat.type in ("group", "supergroup"):
        await message.answer("📩 Я надіслав тобі приватне повідомлення для створення рекомендації.")
        await message.bot.send_message(
            message.from_user.id,
            "Обери тип рекомендації:",
            reply_markup=rec_type_kb()
        )
    else:
        await message.answer("Обери тип рекомендації:", reply_markup=rec_type_kb())

    await state.set_state(CreateRec.choose_type)


@router.callback_query(F.data.startswith("rec:type:"))
async def rec_chosen_type(cb: CallbackQuery, state: FSMContext):
    if cb.message.chat.type != "private":
        return  # FSM працює тільки у приваті

    _, _, type_ = cb.data.split(":")
    await state.update_data(rec_type=type_)
    await cb.message.edit_text("Введи назву:")
    await state.set_state(CreateRec.ask_title)
    await cb.answer()


@router.message(CreateRec.ask_title)
async def rec_ask_desc(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return  # FSM тільки для приватного чату

    await state.update_data(title=message.text.strip())
    await message.answer("Короткий опис:")
    await state.set_state(CreateRec.ask_desc)


@router.message(CreateRec.ask_desc)
async def rec_save(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return  # FSM тільки для приватного чату

    data = await state.get_data()
    type_ = data["rec_type"]
    title = data["title"]
    desc = message.text.strip()

    async with async_session() as db:
        await upsert_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name)
        rec = await add_recommendation(db, message.from_user.id, message.from_user.username, type_, title, desc)

    await message.answer(
        f"✅ Додано!\n\n[{type_.upper()}] {title}\n👤 @{message.from_user.username}\n\n{desc}\n\n"
        f"Можеш поділитися у групі вручну або просто напиши /get_recs там."
    )
    await state.clear()


from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.db import async_session
from app.repositories import list_recommendations

router = Router()

# --- показати вибір категорії
@router.message(F.text == "/get_recs")
async def choose_rec_category(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Фільми", callback_data="recs:movie")],
        [InlineKeyboardButton(text="📺 Серіали", callback_data="recs:series")],
        [InlineKeyboardButton(text="📚 Книги", callback_data="recs:book")],
        [InlineKeyboardButton(text="🎮 Ігри", callback_data="recs:game")],
    ])
    await message.answer("Оберіть категорію рекомендацій:", reply_markup=kb)


# --- показати список рекомендацій по обраній категорії
@router.callback_query(F.data.startswith("recs:"))
async def list_recs_by_category(cb: CallbackQuery):
    type_ = cb.data.split(":")[1]
    async with async_session() as db:
        items = await list_recommendations(db, type_=type_, limit=5)

    icons = {"movie": "🎬", "series": "📺", "book": "📚", "game": "🎮"}
    icon = icons.get(type_, "⭐️")

    if not items:
        await cb.message.edit_text(f"Поки що немає рекомендацій у цій категорії {icon}.")
        return

    text = f"Останні рекомендації ({icon}):\n\n"
    for r in items:
        text += f"• <b>{r.title}</b>\n  👤 @{r.username or 'anon'}\n  💬 {r.description}\n\n"

    await cb.message.edit_text(text, parse_mode="HTML")
