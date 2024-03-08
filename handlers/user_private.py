import os

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import PreCheckoutQuery, LabeledPrice
from dotenv import load_dotenv, find_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from buttons.inline_buttons import MenuCallBack
from database.orm_queries import (
    orm_add_to_cart,
    orm_add_user, orm_get_product,
)
from excel.excel_functional import add_row_to_excel
from handlers.menu_processing import get_menu_content

load_dotenv(find_dotenv())

user_private_router = Router()


class AddShippingInfoToCart(StatesGroup):
    city = State()
    address = State()
    apartment_number = State()


@user_private_router.message(CommandStart())
async def start_command(message: types.Message, session: AsyncSession):
    """Обрабатываем команду старт и запускаем меню"""
    media, reply_markup = await get_menu_content(session, level=0, menu_name="main")

    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


async def add_to_cart(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession):
    """Добавляем товар в корзину"""
    user = callback.from_user
    await orm_add_user(
        session,
        user_id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=None,
    )
    await orm_add_to_cart(session, user_id=user.id, product_id=callback_data.product_id,
                          quantity=callback_data.quantity)
    await callback.answer("Товар добавлен в корзину!")


@user_private_router.callback_query(F.data.startswith('order_'))
async def create_order(callback: types.CallbackQuery, session: AsyncSession):
    """Создаём заказ и отправляем пользователю чек на оплату"""
    user = callback.from_user
    product_id = callback.data.split("_")[-1]
    product = (await orm_get_product(session, int(product_id)))

    await callback.bot.send_invoice(
        chat_id=user.id,
        title=product.description,
        description=product.description,
        payload=str(product.id),
        provider_token=os.getenv('PROVIDER_TOKEN'),
        currency='RUB',
        start_parameter='test_bot',
        prices=[
            LabeledPrice(label='Товар 1', amount=55555),
            LabeledPrice(label='Товар 2', amount=11111),
            LabeledPrice(label='Товар 3', amount=22222)
        ],
        need_shipping_address=True,
    )


@user_private_router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    """Обрабатываем событие pre_checkout и отвечаем пользователю"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@user_private_router.message(F.successful_payment)
async def successful_payment():
    """Добавляем тестовые данные о заказе в таблицу"""
    file_path = './orders.xlsx'
    sheet_name = 'Orders'
    new_row = ['Тестовые данные', 'Тестовые данные', 'Тестовые данные']

    add_row_to_excel(file_path, sheet_name, new_row)


@user_private_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession,
                    ):
    """Выводим пользователю меню"""
    if callback_data.menu_name == "add_to_cart":
        await add_to_cart(callback, callback_data, session)
        return

    media, reply_markup = await get_menu_content(
        session,
        level=callback_data.level,
        menu_name=callback_data.menu_name,
        category=callback_data.category,
        page=callback_data.page,
        product_id=callback_data.product_id,
        user_id=callback.from_user.id,
    )

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()
