import os

from aiogram import Bot, types
from aiogram.filters import Filter
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class ChatTypeFilter(Filter):
    """Регулируем типы чатов"""
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class UserInGroupAndChannelFilter(Filter):
    """Проверяем на то, подписан пользователь на группу и канал"""
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def __call__(self, message: types.Message) -> bool:
        user_in_group = await self.bot.get_chat_member(chat_id=os.getenv('GROUP_ID'), user_id=message.from_user.id)
        user_in_channel = await self.bot.get_chat_member(chat_id=os.getenv('CHANNEL_ID'), user_id=message.from_user.id)

        if user_in_group and user_in_channel:
            return True
