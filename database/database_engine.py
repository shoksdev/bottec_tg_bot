import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.menu_steps import categories, info_pages, subcategories
from database.models import Base
from database.orm_queries import orm_create_categories, orm_add_banner_description, orm_create_subcategories

engine = create_async_engine(os.getenv('DATABASE_ENGINE'), echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    """Создаём БД и добавляем в нее категории и подкатегории"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_create_categories(session, categories)
        await orm_create_subcategories(session, subcategories)
        await orm_add_banner_description(session, info_pages)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
