from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from buttons.inline_buttons import get_callback_buttons
from buttons.reply_buttons import get_keyboard
from database.orm_queries import (
    orm_change_banner_image,
    orm_get_categories,
    orm_add_product,
    orm_get_info_pages,
    orm_update_product, orm_get_subcategories,
)
from filters.chat_types import ChatTypeFilter

admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]))

ADMIN_KB = get_keyboard(
    "Добавить товар",
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)


@admin_router.message(Command("admin"))
async def admin_command(message: types.Message):
    """Обрабатываем команду /admin"""
    await message.answer('Добрый день, я виртуальный помощник для администраторов "BOTTEC", чем я могу быть полезен?',
                         reply_markup=ADMIN_KB)


class AddBanner(StatesGroup):
    image = State()


@admin_router.message(StateFilter(None), F.text == 'Добавить баннер')
async def start_add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    """Инициализируем добавление баннера"""
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\
                         \n{', '.join(pages_names)}")
    await state.set_state(AddBanner.image)


@admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    """Добавляем баннер"""
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите название страницы из списка ниже, например:\
                         \n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id, )
    await message.answer("Баннер добавлен.")
    await state.clear()


@admin_router.message(AddBanner.image)
async def add_banner_exception_error(message: types.Message, state: FSMContext):
    """Обрабатываем неверные данные при добавлении баннера"""
    await message.answer("Отправьте фото баннера или отмена")


class AddProduct(StatesGroup):
    description = State()
    category = State()
    subcategory = State()
    image = State()

    product_for_change = None

    texts = {
        "AddProduct:description": "Введите описание заново:",
        "AddProduct:category": "Выберите категорию  заново",
        "AddProduct:subcategory": "Выберите подкатегорию  заново",
        "AddProduct:image": "Этот шаг последний",
    }


@admin_router.message(StateFilter(None), F.text == "Добавить товар")
async def add_product(message: types.Message, state: FSMContext):
    """Инициализируем добавление товара"""
    await message.answer(
        "Введите описание товара", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddProduct.description)


@admin_router.message(StateFilter("*"), Command("отмена"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    if AddProduct.product_for_change:
        AddProduct.product_for_change = None
    await state.clear()
    await message.answer("Действия отменены", reply_markup=ADMIN_KB)


@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddProduct.description:
        await message.answer(
            'Предыдущего шага нет, или введите название товара или напишите "отмена"'
        )
        return

    previous = None
    for step in AddProduct.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Вы вернулись к прошлому шагу \n {AddProduct.texts[previous.state]}"
            )
            return
        previous = step


@admin_router.message(AddProduct.description, F.text)
async def add_description(message: types.Message, state: FSMContext, session: AsyncSession):
    """Добавляем описание к товару"""
    await state.update_data(description=message.text)

    categories = await orm_get_categories(session)
    buttons = {category.name: str(category.id) for category in categories}
    await message.answer("Выберите категорию", reply_markup=get_callback_buttons(buttons=buttons))
    await state.set_state(AddProduct.category)


@admin_router.message(AddProduct.description)
async def add_description_exception_error(message: types.Message, state: FSMContext):
    """Обрабатываем неверно введенные данные"""
    await message.answer("Вы ввели не допустимые данные, введите текст описания товара")


@admin_router.callback_query(AddProduct.category)
async def category_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    if int(callback.data) in [category.id for category in await orm_get_categories(session)]:
        await callback.answer()
        await state.update_data(category=callback.data)
        subcategories = await orm_get_subcategories(session, category_id=int(callback.data))
        buttons = {subcategory.name: str(subcategory.id) for subcategory in subcategories}
        await callback.message.answer("Выберите подкатегорию", reply_markup=get_callback_buttons(buttons=buttons))
        await state.set_state(AddProduct.subcategory)
    else:
        await callback.message.answer('Выберите категорию из кнопок.')
        await callback.answer()


@admin_router.message(AddProduct.category)
async def category_choice_exception_error(message: types.Message, state: FSMContext):
    """Обрабатываем неверно введенные данные"""
    await message.answer('Выберите категорию из кнопок!')


@admin_router.callback_query(AddProduct.subcategory)
async def subcategory_choice(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Добавляем подкатегорию к товару"""
    data = await state.get_data()
    if int(callback.data) in [subcategory.id for subcategory in
                              await orm_get_subcategories(session, category_id=int(data.get('category')))]:
        await callback.answer()
        await state.update_data(subcategory=callback.data)
        await callback.message.answer("Загрузите изображение товара")
        await state.set_state(AddProduct.image)
    else:
        await callback.message.answer('Выберите подкатегорию из кнопок!')
        await callback.answer()


@admin_router.message(AddProduct.subcategory)
async def subcategory_choice_exception_error(message: types.Message, state: FSMContext):
    """Обрабатываем неверно введенные данные"""
    await message.answer('Выберите подкатегорию из кнопок!')


@admin_router.message(AddProduct.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    """Добавляем картинку к товару"""
    if message.text and message.text == "." and AddProduct.product_for_change:
        await state.update_data(image=AddProduct.product_for_change.image)

    elif message.photo:
        await state.update_data(image=message.photo[-1].file_id)
    else:
        await message.answer("Отправьте фото!")
        return
    data = await state.get_data()
    try:
        if AddProduct.product_for_change:
            await orm_update_product(session, AddProduct.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар добавлен/изменен", reply_markup=ADMIN_KB)
        await state.clear()

    except Exception as e:
        await message.answer(
            f"Ошибка: \n{str(e)}",
            reply_markup=ADMIN_KB,
        )
        await state.clear()

    AddProduct.product_for_change = None


@admin_router.message(AddProduct.image)
async def add_image_exception_error(message: types.Message, state: FSMContext):
    """Обрабатываем неверно введенные данные"""
    await message.answer("Отправьте фото!")
