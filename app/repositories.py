from typing import Sequence, Optional
from sqlalchemy import select, desc, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Users, Recommendations, Quizzes, Questions, QuizResults

# -------- Users
async def upsert_user(db: AsyncSession, user_id: int, username: Optional[str], first_name: Optional[str]):
    user = await db.get(Users, user_id)
    if user:
        user.username = username
        user.first_name = first_name
    else:
        user = Users(user_id=user_id, username=username, first_name=first_name)
        db.add(user)
    await db.commit()

# -------- Recommendations
async def add_recommendation(db: AsyncSession, user_id: int, username: str | None, type_: str, title: str, description: str):
    rec = Recommendations(user_id=user_id, username=username, type=type_, title=title, description=description)
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec

async def list_recommendations(db: AsyncSession, type_: str, limit: int = 5, offset: int = 0) -> Sequence[Recommendations]:
    q = select(Recommendations).where(Recommendations.type == type_).order_by(desc(Recommendations.created_at)).limit(limit).offset(offset)
    res = await db.execute(q)
    return res.scalars().all()

async def weekly_recommendations(db: AsyncSession) -> Sequence[Recommendations]:
    q = select(Recommendations).where(Recommendations.created_at >= func.now() - text("interval '7 days'")).order_by(desc(Recommendations.created_at))
    res = await db.execute(q)
    return res.scalars().all()

# -------- Quizzes & Questions
async def create_quiz(db: AsyncSession, title: str, type_: str, description: str | None, created_by: int | None) -> Quizzes:
    quiz = Quizzes(title=title, type=type_, description=description, created_by=created_by)
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    return quiz

async def add_question(db: AsyncSession, quiz_id: int, text_: str, a: str, b: str, c: str, correct: str, created_by: int | None, is_approved: bool = False) -> Questions:
    q = Questions(quiz_id=quiz_id, text=text_, option_a=a, option_b=b, option_c=c, correct_option=correct, created_by=created_by, is_approved=is_approved)
    db.add(q)
    await db.commit()
    await db.refresh(q)
    return q

async def list_quizzes_by_type(db: AsyncSession, type_: str) -> Sequence[Quizzes]:
    q = select(Quizzes).where(Quizzes.type == type_).order_by(desc(Quizzes.created_at))
    res = await db.execute(q)
    return res.scalars().all()

async def list_approved_questions(db: AsyncSession, quiz_id: int) -> Sequence[Questions]:
    q = select(Questions).where(and_(Questions.quiz_id == quiz_id, Questions.is_approved == True)).order_by(Questions.id)
    res = await db.execute(q)
    return res.scalars().all()

async def get_quiz(db: AsyncSession, quiz_id: int) -> Optional[Quizzes]:
    return await db.get(Quizzes, quiz_id)

async def get_pending_questions(db: AsyncSession, limit: int = 1) -> Sequence[Questions]:
    q = select(Questions).where(Questions.is_approved == False).order_by(Questions.created_at).limit(limit)
    res = await db.execute(q)
    return res.scalars().all()

async def approve_question(db: AsyncSession, question_id: int, approve: bool):
    q = await db.get(Questions, question_id)
    if not q:
        return
    if approve:
        q.is_approved = True
    else:
        await db.delete(q)
    await db.commit()

# -------- Results & Leaders
async def save_quiz_result(db: AsyncSession, user_id: int, username: str | None, quiz_id: int, score: int, total: int):
    r = QuizResults(user_id=user_id, username=username, quiz_id=quiz_id, score=score, total=total)
    db.add(r)
    await db.commit()
    return r

async def top3_by_category(db: AsyncSession, category: str):
    """
    Топ-3 користувачів для категорії (book/movie/series/game):
    — Беремо ЛИШЕ квізи цієї категорії.
    — Для кожного user_id: найкращий відсоток (score/total) серед усіх спроб у категорії.
    — При однаковому відсотку перемагає той, у кого пізніший completed_at.
    """
    # SQL через window functions для стислості
    sql = f"""
    with cat_quizzes as (
      select id from quizzes where type = :cat
    ),
    ranked as (
      select
        r.user_id,
        coalesce(r.username, '') as username,
        r.completed_at,
        (r.score::float / nullif(r.total,0)) as pct,
        row_number() over (
          partition by r.user_id
          order by (r.score::float/nullif(r.total,0)) desc nulls last, r.completed_at desc
        ) as rn
      from quiz_results r
      where r.quiz_id in (select id from cat_quizzes)
    ),
    best as (
      select user_id, username, pct, completed_at
      from ranked where rn = 1
      order by pct desc nulls last, completed_at desc
      limit 3
    )
    select * from best;
    """
    res = await db.execute(text(sql), {"cat": category})
    rows = res.mappings().all()
    return rows

# -------- User-specific results
async def user_results(db: AsyncSession, user_id: int):
    """
    Повертає всі результати користувача (назва квізу, категорія, %)
    """
    sql = """
    SELECT q.title, q.type, r.score, r.total,
           (r.score::float / NULLIF(r.total, 0)) * 100 AS pct
    FROM quiz_results r
    JOIN quizzes q ON q.id = r.quiz_id
    WHERE r.user_id = :user_id
    ORDER BY r.completed_at DESC
    """
    res = await db.execute(text(sql), {"user_id": user_id})
    rows = res.mappings().all()
    return rows

