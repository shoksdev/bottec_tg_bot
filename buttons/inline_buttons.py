from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuCallBack(CallbackData, prefix="menu"):
    """Создаём колбек меню"""
    level: int
    menu_name: str
    category: int | None = None
    page: int = 1
    product_id: int | None = None
    quantity: int | None = None


def get_user_main_buttons(*, level: int, sizes: tuple[int] = (2,)):
    """Создаём меню кнопок при вводе команды /start"""
    keyboard = InlineKeyboardBuilder()
    buttons = {
        "Каталог": "catalog",
        "Корзина": "cart",
        "FAQ": "faq",
    }
    for text, menu_name in buttons.items():
        if menu_name == 'catalog':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level + 1, menu_name=menu_name).pack()))
        elif menu_name == 'subcatalog':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level + 1, menu_name=menu_name).pack()))
        elif menu_name == 'cart':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=5, menu_name=menu_name).pack()))
        elif menu_name == 'faq':
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=6, menu_name=menu_name).pack()))
        else:
            keyboard.add(InlineKeyboardButton(text=text,
                                              callback_data=MenuCallBack(level=level, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_user_catalog_buttons(*, level: int, categories: list, sizes: tuple[int] = (2,)):
    """Создаём меню кнопок при переходе в каталог"""
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='На главную',
                                      callback_data=MenuCallBack(level=0, menu_name='main').pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина',
                                      callback_data=MenuCallBack(level=5, menu_name='cart').pack()))

    for category in categories:
        keyboard.add(InlineKeyboardButton(text=category.name,
                                          callback_data=MenuCallBack(level=level + 1, menu_name=category.name,
                                                                     category=category.id).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_products_buttons(
        *,
        level: int,
        category: int,
        page: int,
        pagination_buttons: dict,
        product_id: int,
        sizes: tuple[int] = (2, 1)
):
    """Создаем меню кнопок при переходе в подкатегории"""
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='В каталог',
                                      callback_data=MenuCallBack(level=1, menu_name='catalog').pack()))
    keyboard.add(InlineKeyboardButton(text='Корзина',
                                      callback_data=MenuCallBack(level=5, menu_name='cart').pack()))
    keyboard.add(InlineKeyboardButton(text='Заказать',
                                      callback_data=MenuCallBack(level=4, menu_name='precart',
                                                                 product_id=product_id).pack()))

    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_buttons.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                category=category,
                                                page=page + 1).pack()))

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                category=category,
                                                page=page - 1).pack()))

    return keyboard.row(*row).as_markup()


def get_questions_buttons(
        *,
        level: int,
        page: int,
        pagination_buttons: dict,
        sizes: tuple[int] = (2, 1)
):
    """Создаём меню кнопок для работы с FAQ"""
    keyboard = InlineKeyboardBuilder()

    keyboard.add(InlineKeyboardButton(text='На главную',
                                      callback_data=MenuCallBack(level=0, menu_name='main').pack()))

    keyboard.adjust(*sizes)

    row = []
    for text, menu_name in pagination_buttons.items():
        if menu_name == "next":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                page=page + 1).pack()))

        elif menu_name == "previous":
            row.append(InlineKeyboardButton(text=text,
                                            callback_data=MenuCallBack(
                                                level=level,
                                                menu_name=menu_name,
                                                page=page - 1).pack()))

    return keyboard.row(*row).as_markup()


def get_user_precart(
        *,
        level: int,
        page: int | None,
        product_id: int | None,
        sizes: tuple[int] = (3,)
):
    """Создаём меню при добавлении товара в корзину, даем возможность пользователю изменить количество товара"""
    keyboard = InlineKeyboardBuilder()
    if page:
        keyboard.add(InlineKeyboardButton(text='-1',
                                          callback_data=MenuCallBack(level=level, menu_name='decrement',
                                                                     product_id=product_id, page=page).pack()))
        keyboard.add(InlineKeyboardButton(text='+1',
                                          callback_data=MenuCallBack(level=level, menu_name='increment',
                                                                     product_id=product_id, page=page).pack()))

        keyboard.adjust(*sizes)

        row = []

        keyboard.row(*row)

        row2 = [
            InlineKeyboardButton(text='На главную',
                                 callback_data=MenuCallBack(level=0, menu_name='main').pack()),
            InlineKeyboardButton(text='Подтвердить',
                                 callback_data=MenuCallBack(level=level, menu_name='add_to_cart',
                                                            product_id=product_id, quantity=page).pack()),
            InlineKeyboardButton(text='Корзина',
                                 callback_data=MenuCallBack(level=5, menu_name='cart').pack())
        ]
        return keyboard.row(*row2).as_markup()
    else:
        keyboard.add(
            InlineKeyboardButton(text='На главную',
                                 callback_data=MenuCallBack(level=0, menu_name='main').pack()))

        return keyboard.adjust(*sizes).as_markup()


def get_user_cart(
        *,
        level: int,
        page: int | None,
        pagination_buttons: dict | None,
        product_id: int | None,
        sizes: tuple[int] = (3,)
):
    """Создаём меню при переходе в корзину"""
    keyboard = InlineKeyboardBuilder()
    if page:
        keyboard.add(InlineKeyboardButton(text='Удалить',
                                          callback_data=MenuCallBack(level=level, menu_name='delete',
                                                                     product_id=product_id, page=page).pack()))

        keyboard.adjust(*sizes)

        row = []
        for text, menu_name in pagination_buttons.items():
            if menu_name == "next":
                row.append(InlineKeyboardButton(text=text,
                                                callback_data=MenuCallBack(level=level, menu_name=menu_name,
                                                                           page=page + 1).pack()))
            elif menu_name == "previous":
                row.append(InlineKeyboardButton(text=text,
                                                callback_data=MenuCallBack(level=level, menu_name=menu_name,
                                                                           page=page - 1).pack()))

        keyboard.row(*row)

        row2 = [
            InlineKeyboardButton(text='На главную',
                                 callback_data=MenuCallBack(level=0, menu_name='main').pack()),
            InlineKeyboardButton(text='Заказать',
                                 callback_data=f'order_{product_id}'),
        ]
        return keyboard.row(*row2).as_markup()
    else:
        keyboard.add(
            InlineKeyboardButton(text='На главную',
                                 callback_data=MenuCallBack(level=0, menu_name='main').pack()))

        return keyboard.adjust(*sizes).as_markup()


def get_callback_buttons(*, buttons: dict[str, str], sizes: tuple[int] = (2,)):
    """Создаём меню для вывода конкретных кнопок"""
    keyboard = InlineKeyboardBuilder()

    for text, data in buttons.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=data))

    return keyboard.adjust(*sizes).as_markup()
