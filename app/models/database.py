import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

load_dotenv()


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")

Base = declarative_base()

engine =  create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, 
    expire_on_commit=False,
    autocommit=False, 
    autoflush=False, 
    class_=AsyncSession
)

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()