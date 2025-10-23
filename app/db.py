from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

async def init_db():
    from app.models import Users, Recommendations, Quizzes, Questions, QuizResults  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
