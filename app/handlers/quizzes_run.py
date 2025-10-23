import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.fsm.states import RunQuiz
from app.keyboards import categories_kb
from app.db import async_session
from app.repositories import (
    list_quizzes_by_type,
    list_approved_questions,
    save_quiz_result,
    upsert_user,
)
from app.models import Questions

router = Router()


# --- запуск квізу ---
@router.message(F.text == "/quiz")
async def quiz_entry(message: Message, state: FSMContext):
    if message.chat.type in ("group", "supergroup"):
        await message.answer("📩 Надіслав квіз у приватні повідомлення!")
        await message.bot.send_message(
            message.from_user.id, "Обери категорію квізу:", reply_markup=categories_kb("rq")
        )
    else:
        await message.answer("Обери категорію квізу:", reply_markup=categories_kb("rq"))
    await state.set_state(RunQuiz.choose_cat)


# --- вибір категорії ---
@router.callback_query(F.data.startswith("rq:cat:"))
async def rq_pick_category(cb: CallbackQuery, state: FSMContext):
    _, _, cat = cb.data.split(":")
    async with async_session() as db:
        quizzes = await list_quizzes_by_type(db, cat)
    if not quizzes:
        await cb.message.edit_text("Поки що немає квізів у цій категорії.")
        await cb.answer()
        return

    text = "Оберіть квіз, надіславши його номер:\n\n"
    for i, q in enumerate(quizzes[:10], start=1):
        text += f"{i}) {q.title}\n"
    await cb.message.edit_text(text + "\nВідправ цифру (1-10) обраного квізу.")
    await state.update_data(cat=cat, quiz_ids=[q.id for q in quizzes[:10]])
    await state.set_state(RunQuiz.choose_quiz)
    await cb.answer()


# --- вибір конкретного квізу ---
@router.message(RunQuiz.choose_quiz)
async def rq_choose_quiz(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        idx = int(message.text.strip()) - 1
    except ValueError:
        await message.answer("Надішли номер квізу цифрою.")
        return

    quiz_ids = data["quiz_ids"]
    if idx < 0 or idx >= len(quiz_ids):
        await message.answer("Невірний номер. Спробуй ще.")
        return

    quiz_id = quiz_ids[idx]
    async with async_session() as db:
        qs = await list_approved_questions(db, quiz_id)

    if len(qs) == 0:
        await message.answer("У цього квізу поки немає затверджених питань.")
        await state.clear()
        return

    random.shuffle(qs)
    qs = qs[:20] if len(qs) > 20 else qs
    await state.update_data(quiz_id=quiz_id, questions=[q.id for q in qs], idx=0, score=0)

    q = qs[0]
    body = (
        f"❓ Питання 1/{len(qs)}\n\n"
        f"{q.text}\n"
        f"А) {q.option_a}\nБ) {q.option_b}\nВ) {q.option_c}"
    )

    # нова клавіатура з кириличними літерами
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for opt in ("А", "Б", "В"):
        kb.button(text=opt, callback_data=f"rq:ans:{quiz_id}:{q.id}:{opt}")
    kb.adjust(3)

    await message.answer(body, reply_markup=kb.as_markup())
    await state.set_state(RunQuiz.answering)


# --- перевірка відповіді ---
@router.callback_query(F.data.startswith("rq:ans:"))
async def rq_answer(cb: CallbackQuery, state: FSMContext):
    _, _, quiz_id, qid, chosen = cb.data.split(":")
    quiz_id = int(quiz_id)
    qid = int(qid)

    data = await state.get_data()
    if data.get("quiz_id") != quiz_id:
        await cb.answer("Це не твій активний квіз.", show_alert=True)
        return

    async with async_session() as db:
        q = await db.get(Questions, qid)

    if not q:
        await cb.answer("Питання не знайдено", show_alert=True)
        return

    score = data.get("score", 0)
    total_q = len(data["questions"])

    if chosen == q.correct_option:
        score += 1

    idx = data["idx"] + 1

    # завершення
    if idx >= total_q:
        async with async_session() as db:
            await upsert_user(db, cb.from_user.id, cb.from_user.username, cb.from_user.first_name)
            await save_quiz_result(db, cb.from_user.id, cb.from_user.username, quiz_id, score, total_q)
        percent = round(100 * score / total_q)
        await cb.message.edit_text(f"✅ Результат: {score}/{total_q} ({percent}%)")
        await state.clear()
        await cb.answer()
        return

    # наступне питання
    async with async_session() as db:
        next_q = await db.get(Questions, data["questions"][idx])

    body = (
        f"❓ Питання {idx+1}/{total_q}\n\n"
        f"{next_q.text}\n"
        f"А) {next_q.option_a}\nБ) {next_q.option_b}\nВ) {next_q.option_c}"
    )

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    for opt in ("А", "Б", "В"):
        kb.button(text=opt, callback_data=f"rq:ans:{quiz_id}:{next_q.id}:{opt}")
    kb.adjust(3)

    await state.update_data(idx=idx, score=score)
    await cb.message.edit_text(body, reply_markup=kb.as_markup())
    await cb.answer()
