import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dotenv import find_dotenv, load_dotenv

from filters.chat_types import ChatTypeFilter, UserInGroupAndChannelFilter
from handlers.admin_private import admin_router

load_dotenv(find_dotenv())

from middleware.database_middlewares import DataBaseSession

from database.database_engine import create_db, session_maker

from handlers.user_private import user_private_router

bot = Bot(token=os.getenv('TELEGRAM_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(admin_router)
user_private_router.message.filter(ChatTypeFilter(["private"]), UserInGroupAndChannelFilter(bot))


async def on_startup(bot):
    await create_db()


async def main():
    dp.startup.register(on_startup)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
