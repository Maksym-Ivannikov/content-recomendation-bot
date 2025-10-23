from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.fsm.states import CreateQuiz
from app.keyboards import categories_kb
from app.db import async_session
from app.repositories import create_quiz, add_question, upsert_user, list_quizzes_by_type
from sqlalchemy import select
from app.models import Quizzes

router = Router()


# --- 1️⃣ Створення нового квізу ---
@router.message(F.text == "/create_quiz")
async def create_quiz_entry(message: Message, state: FSMContext):
    if message.chat.type in ("group", "supergroup"):
        await message.answer("📩 Я надіслав тобі приватне повідомлення для створення квізу.")
        await message.bot.send_message(message.from_user.id, "Введи назву квізу:")
    else:
        await message.answer("Введи назву квізу:")
    await state.set_state(CreateQuiz.ask_title)


@router.message(CreateQuiz.ask_title)
async def cq_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("Обери категорію:", reply_markup=categories_kb("cq"))
    await state.set_state(CreateQuiz.ask_type)


@router.callback_query(F.data.startswith("cq:cat:"))
async def cq_type(cb: CallbackQuery, state: FSMContext):
    _, _, type_ = cb.data.split(":")
    await state.update_data(type=type_)
    await cb.message.edit_text("Короткий опис (можна пропустити, надішли '-'):")
    await state.set_state(CreateQuiz.ask_desc)
    await cb.answer()


@router.message(CreateQuiz.ask_desc)
async def cq_desc(message: Message, state: FSMContext):
    desc = None if message.text.strip() == "-" else message.text.strip()
    data = await state.get_data()

    async with async_session() as db:
        await upsert_user(db, message.from_user.id, message.from_user.username, message.from_user.first_name)

        # Створюємо новий квіз
        quiz = await create_quiz(db, data["title"], data["type"], desc, message.from_user.id)

    await state.update_data(quiz_id=quiz.id)
    await message.answer("✅ Квіз створено. Додамо перше питання.\nНадішли текст питання:")
    await state.set_state(CreateQuiz.q_text)


# --- 2️⃣ Додавання питання до ІСНУЮЧОГО квізу ---
@router.message(F.text == "/add_question")
async def aq_entry(message: Message, state: FSMContext):
    await message.answer("Оберіть категорію квізу, до якого хочеш додати питання:", reply_markup=categories_kb("aq"))
    await state.set_state(CreateQuiz.choose_type)


@router.callback_query(F.data.startswith("aq:cat:"))
async def aq_choose_quiz(cb: CallbackQuery, state: FSMContext):
    _, _, type_ = cb.data.split(":")
    async with async_session() as db:
        quizzes = await list_quizzes_by_type(db, type_)
    if not quizzes:
        await cb.message.edit_text("❌ У цій категорії ще немає квізів.")
        await state.clear()
        await cb.answer()
        return

    # створюємо інлайн-кнопки зі списком квізів
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=q.title[:40], callback_data=f"aq:quiz:{q.id}")]
            for q in quizzes[:10]
        ]
    )
    await cb.message.edit_text(f"Оберіть квіз у категорії ({type_}):", reply_markup=kb)
    await state.update_data(type=type_)
    await cb.answer()


@router.callback_query(F.data.startswith("aq:quiz:"))
async def aq_selected_quiz(cb: CallbackQuery, state: FSMContext):
    _, _, quiz_id = cb.data.split(":")
    await state.update_data(quiz_id=int(quiz_id))
    await cb.message.edit_text("Введи текст питання:")
    await state.set_state(CreateQuiz.q_text)
    await cb.answer()


# --- 3️⃣ /finish у будь-якому стані ---
@router.message(F.text.regexp(r"^/(finish|done|готово)(@.+)?$"))
async def cq_finish(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state and current_state.startswith("CreateQuiz"):
        await message.answer("✅ Створення питань завершено. Вони відправлені на модерацію.")
        await state.clear()


# --- 4️⃣ Логіка додавання питань (спільна для обох режимів) ---
@router.message(CreateQuiz.q_text, ~F.text.startswith("/"))
async def cq_q_text(message: Message, state: FSMContext):
    await state.update_data(q_text=message.text.strip())
    await message.answer("Варіанти через кому (А,Б,В):")
    await state.set_state(CreateQuiz.q_options)


@router.message(CreateQuiz.q_options, ~F.text.startswith("/"))
async def cq_q_options(message: Message, state: FSMContext):
    parts = [p.strip() for p in message.text.split(",")]
    if len(parts) < 3:
        await message.answer("Потрібно три варіанти. Спробуй ще раз (А,Б,В):")
        return
    await state.update_data(optA=parts[0], optB=parts[1], optC=parts[2])
    await message.answer("Яка правильна відповідь? (А/Б/В)")
    await state.set_state(CreateQuiz.q_correct)


@router.message(CreateQuiz.q_correct, ~F.text.startswith("/"))
async def cq_q_correct(message: Message, state: FSMContext):
    correct = message.text.strip().upper()
    if correct not in ("А", "Б", "В"):
        await message.answer("Вкажи А/Б/В:")
        return

    data = await state.get_data()
    async with async_session() as db:
        await add_question(
            db,
            quiz_id=data["quiz_id"],
            text_=data["q_text"],
            a=data["optA"],
            b=data["optB"],
            c=data["optC"],
            correct=correct,
            created_by=message.from_user.id,
            is_approved=False
        )

    await message.answer(
        "✅ Питання додано та відправлено на верифікацію.\n"
        "Додати ще? Надішли наступний текст питання або /finish, щоб завершити."
    )
    await state.set_state(CreateQuiz.q_text)
