from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from buttons.inline_buttons import (
    get_products_buttons,
    get_user_cart,
    get_user_catalog_buttons,
    get_user_main_buttons, get_user_precart, get_questions_buttons,
)
from database.orm_queries import Paginator
from database.orm_queries import (
    orm_delete_from_cart,
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    orm_get_user_carts,
    orm_get_subcategories, orm_get_product, orm_get_questions,
)


async def main_menu(session: AsyncSession, level: int, menu_name: str):
    """Создаём главное меню"""
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    keyboard = get_user_main_buttons(level=level)

    return image, keyboard


async def catalog(session: AsyncSession, level: int, menu_name: str):
    """Создаём каталог"""
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_categories(session)

    keyboard = get_user_catalog_buttons(level=level, categories=categories)

    return image, keyboard


async def subcatalog(session: AsyncSession, level: int, category: int, menu_name: str):
    """Создаём подкаталог (с подкатегориями)"""
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_subcategories(session, category_id=category)

    keyboard = get_user_catalog_buttons(level=level, categories=categories)

    return image, keyboard


def pages(paginator: Paginator):
    """Выводим функционал переключения страниц в пагинации"""
    buttons = dict()
    if paginator.has_previous():
        buttons["◀ Пред."] = "previous"

    if paginator.has_next():
        buttons["След. ▶"] = "next"

    return buttons


async def get_all_products(session: AsyncSession, level: int, subcategory: int, page: int):
    """Выводим все товары"""
    products = await orm_get_products(session, subcategory_id=subcategory)

    paginator = Paginator(products, page=page)
    product = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=product.image,
        caption=f"{product.description}\n"
                f"<strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )

    pagination_buttons = pages(paginator)

    keyboard = get_products_buttons(
        level=level,
        category=subcategory,
        page=page,
        pagination_buttons=pagination_buttons,
        product_id=product.id,
    )

    return image, keyboard


async def get_all_questions(session: AsyncSession, level: int, page: int):
    """Выводим все вопросы (FAQ)"""
    questions = await orm_get_questions(session)
    banner = (await orm_get_banner(session, page='faq'))
    paginator = Paginator(questions, page=page)
    question = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=banner.image,
        caption=f"Вопрос: {question.question}\nОтвет: {question.answer}",
    )

    pagination_buttons = pages(paginator)

    keyboard = get_questions_buttons(
        level=level,
        page=page,
        pagination_buttons=pagination_buttons,
    )

    return image, keyboard


async def precart(session: AsyncSession, level: int, menu_name: str, page: int, product_id: int):
    """Выводим добавление товара в корзину (изменение количества и подтверждение)"""
    product = (await orm_get_product(session, product_id))
    if menu_name == "decrement":
        if product.quantity > 1 or page > 1:
            page -= 1
        else:
            page = 0
    elif menu_name == "increment":
        page += 1

    image = InputMediaPhoto(
        media=product.image,
        caption=f"{product.description}\nКоличество: {page}"
    )
    keyboard = get_user_precart(
        level=level,
        page=page,
        product_id=product_id,
    )

    return image, keyboard


async def get_cart(session: AsyncSession, level: int, menu_name: str, page: int, user_id: int, product_id: int):
    """Создаем корзину для пользователя"""
    if menu_name == "delete":
        await orm_delete_from_cart(session, user_id, product_id)
        if page > 1:
            page -= 1

    carts = await orm_get_user_carts(session, user_id)

    if not carts:
        banner = await orm_get_banner(session, "cart")
        image = InputMediaPhoto(
            media=banner.image, caption=f"<strong>{banner.description}</strong>"
        )

        keyboard = get_user_cart(
            level=level,
            page=None,
            pagination_buttons=None,
            product_id=None,
        )
    else:
        paginator = Paginator(carts, page=page)

        cart = paginator.get_page()[0]

        image = InputMediaPhoto(
            media=cart.product.image,
            caption=f"{cart.product.description}\nКоличество: {cart.quantity}"
                    f"\nТовар {paginator.page} из {paginator.pages} в корзине."
        )

        pagination_buttons = pages(paginator)

        keyboard = get_user_cart(
            level=level,
            page=page,
            pagination_buttons=pagination_buttons,
            product_id=cart.product.id,
        )

    return image, keyboard


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
        product_id: int | None = None,
        user_id: int | None = None,
):
    """Объединяем все функции выше и выводим их в соответствии с их уровнем"""
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await subcatalog(session, level, category, menu_name)
    elif level == 3:
        return await get_all_products(session, level, category, page)
    elif level == 4:
        return await precart(session, level, menu_name, page, product_id)
    elif level == 5:
        return await get_cart(session, level, menu_name, page, user_id, product_id)
    elif level == 6:
        return await get_all_questions(session, level, page)
