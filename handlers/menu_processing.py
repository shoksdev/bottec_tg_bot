from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_queries import (
    orm_add_to_cart,
    orm_delete_from_cart,
    orm_get_banner,
    orm_get_categories,
    orm_get_products,
    orm_get_user_carts,
    orm_reduce_product_in_cart, orm_get_subcategories, orm_get_product, orm_get_questions,
)
from buttons.inline import (
    get_products_btns,
    get_user_cart,
    get_user_catalog_btns,
    get_user_main_btns, get_user_precart, get_questions_btns,
)

from database.orm_queries import Paginator


async def main_menu(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns(level=level)

    return image, kbds


async def catalog(session, level, menu_name):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_categories(session)

    kbds = get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


async def catalog2(session, level, menu_name, category):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    categories = await orm_get_subcategories(session, category_id=category)

    kbds = get_user_catalog_btns(level=level, categories=categories)

    return image, kbds


def pages(paginator: Paginator):
    btns = dict()
    if paginator.has_previous():
        btns["◀ Пред."] = "previous"

    if paginator.has_next():
        btns["След. ▶"] = "next"

    return btns


async def products(session, level, subcategory, page):
    products = await orm_get_products(session, subcategory_id=subcategory)

    paginator = Paginator(products, page=page)
    product = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=product.image,
        caption=f"{product.description}\n"
                f"<strong>Товар {paginator.page} из {paginator.pages}</strong>",
    )

    pagination_btns = pages(paginator)

    kbds = get_products_btns(
        level=level,
        category=subcategory,
        page=page,
        pagination_btns=pagination_btns,
        product_id=product.id,
    )

    return image, kbds


async def questions(session, level, page):
    questions = await orm_get_questions(session)
    banner = (await orm_get_banner(session, page='faq'))
    paginator = Paginator(questions, page=page)
    question = paginator.get_page()[0]

    image = InputMediaPhoto(
        media=banner.image,
        caption=f"Вопрос: {question.question}\nОтвет: {question.answer}",
    )

    pagination_btns = pages(paginator)

    kbds = get_questions_btns(
        level=level,
        page=page,
        pagination_btns=pagination_btns,
    )

    return image, kbds


async def precart(session, level, menu_name, page, product_id):
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
    kbds = get_user_precart(
        level=level,
        page=page,
        product_id=product_id,
    )

    return image, kbds


async def cart(session, level, menu_name, page, user_id, product_id):
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

        kbds = get_user_cart(
            level=level,
            page=None,
            pagination_btns=None,
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

        pagination_btns = pages(paginator)

        kbds = get_user_cart(
            level=level,
            page=page,
            pagination_btns=pagination_btns,
            product_id=cart.product.id,
        )

    return image, kbds


async def get_menu_content(
        session: AsyncSession,
        level: int,
        menu_name: str,
        category: int | None = None,
        page: int | None = None,
        product_id: int | None = None,
        user_id: int | None = None,
):
    if level == 0:
        return await main_menu(session, level, menu_name)
    elif level == 1:
        return await catalog(session, level, menu_name)
    elif level == 2:
        return await catalog2(session, level, category=category, menu_name='subcatalog')
    elif level == 3:
        return await products(session, level, category, page)
    elif level == 4:
        return await precart(session, level, menu_name, page, product_id)
    elif level == 5:
        return await cart(session, level, menu_name, page, user_id, product_id)
    elif level == 6:
        return await questions(session, level, page)