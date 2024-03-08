import math

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Banner, Cart, Category, Product, User, SubCategory, Question


class Paginator:
    """Простенький пагинатор"""
    def __init__(self, array: list | tuple, page: int = 1, per_page: int = 1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        self.pages = math.ceil(self.len / self.per_page)

    def __get_slice(self):
        """Получаем срез страниц"""
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def get_page(self):
        """Получаем текущую страницу"""
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        """Переходим на следующую страницу"""
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        """Переходим на предыдущую страницу"""
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self):
        """Получаем следующую страницу"""
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError(f'Next page does not exist. Use has_next() to check before.')

    def get_previous(self):
        """Получаем предыдущую страницу"""
        if self.page > 1:
            self.page -= 1
            return self.__get_slice()
        raise IndexError(f'Previous page does not exist. Use has_previous() to check before.')


async def orm_add_banner_description(session: AsyncSession, data: dict):
    """Добавляем описание баннера из модели"""
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    """Получаем баннер из модели и изменяем изображение на нём"""
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    """Получаем баннер из модели"""
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_info_pages(session: AsyncSession):
    """Получаем все баннеры из модели"""
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_categories(session: AsyncSession):
    """Получаем все категории из модели"""
    query = select(Category)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_subcategories(session: AsyncSession, category_id):
    """Получаем все подкатегории категории из модели"""
    query = select(SubCategory).where(SubCategory.category_id == int(category_id))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_create_categories(session: AsyncSession, categories: list):
    """Создаем все категории в БД из списка"""
    query = select(Category)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Category(name=name) for name in categories])
    await session.commit()


async def orm_create_subcategories(session: AsyncSession, subcategories: list):
    """Создаем все подкатегории в БД из списка"""
    query = select(SubCategory)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([SubCategory(category_id=subcategory[0], name=subcategory[1]) for subcategory in subcategories])
    await session.commit()


async def orm_add_product(session: AsyncSession, data: dict):
    """Добавляем товар в БД"""
    obj = Product(
        description=data["description"],
        image=data["image"],
        subcategory_id=int(data["subcategory"]),
    )
    session.add(obj)
    await session.commit()


async def orm_get_products(session: AsyncSession, subcategory_id):
    """Получаем все товары подкатегории"""
    query = select(Product).where(Product.subcategory_id == int(subcategory_id))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_product(session: AsyncSession, product_id: int):
    """Получаем товар"""
    query = select(Product).where(Product.id == product_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_update_product(session: AsyncSession, product_id: int, data):
    """Изменяем товар"""
    query = (
        update(Product)
        .where(Product.id == product_id)
        .values(
            description=data["description"],
            image=data["image"],
            category_id=int(data["category"]),
        )
    )
    await session.execute(query)
    await session.commit()


async def orm_delete_product(session: AsyncSession, product_id: int):
    """Удаляем товар"""
    query = delete(Product).where(Product.id == product_id)
    await session.execute(query)
    await session.commit()


async def orm_add_user(
        session: AsyncSession,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
):
    """Добавляем пользователя"""
    query = select(User).where(User.user_id == user_id)
    result = await session.execute(query)
    if result.first() is None:
        session.add(
            User(user_id=user_id, first_name=first_name, last_name=last_name, phone=phone)
        )
        await session.commit()


async def orm_add_to_cart(session: AsyncSession, user_id: int, product_id: int, quantity: int):
    """Создаём корзину, если ее нет у пользователя или добавляем в нее товар"""
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id).options(joinedload(Cart.product))
    cart = await session.execute(query)
    cart = cart.scalar()
    if cart:
        cart.quantity += quantity
        await session.commit()
        return cart
    else:
        session.add(Cart(user_id=user_id, product_id=product_id, quantity=quantity))
        await session.commit()


async def orm_get_user_carts(session: AsyncSession, user_id):
    """Получаем товары из корзины пользователя"""
    query = select(Cart).filter(Cart.user_id == user_id).options(joinedload(Cart.product))
    result = await session.execute(query)
    return result.scalars().all()


async def orm_delete_from_cart(session: AsyncSession, user_id: int, product_id: int):
    """Удаляем товар из корзины"""
    query = delete(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id)
    await session.execute(query)
    await session.commit()


async def orm_reduce_product_in_cart(session: AsyncSession, user_id: int, product_id: int):
    """Изменяем товар из корзины"""
    query = select(Cart).where(Cart.user_id == user_id, Cart.product_id == product_id).options(joinedload(Cart.product))
    cart = await session.execute(query)
    cart = cart.scalar()

    if not cart:
        return
    if cart.quantity > 1:
        cart.quantity -= 1
        await session.commit()
        return True
    else:
        await orm_delete_from_cart(session, user_id, product_id)
        await session.commit()
        return False


async def orm_get_questions(session: AsyncSession):
    """Получаем все вопросы из модели"""
    query = select(Question)
    result = await session.execute(query)
    return result.scalars().all()
