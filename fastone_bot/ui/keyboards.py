from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import fastone_bot.ui.formatters as formatters
import fastone_bot.payments.yookassa as yookassa
from fastone_bot.core.models import Payments
from fastone_bot.core import requests as rq

main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='🚀 Оформить подписку')],
        [
            KeyboardButton(text='👤 Личный кабинет'),
            KeyboardButton(text='ℹ️ Информация')
        ],
        [
            KeyboardButton(text='📡 Мои подписки'),
            KeyboardButton(text='💳 Платежи')
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder='Выберите действие...')

values_of_subs = [1, 3, 6, 9, 12]
async def subs_value(param, user):
    keyboard = []
    for value in values_of_subs:
        keyboard.append([
            InlineKeyboardButton(text=f'🔥 {value} Мес. - {formatters.format_cost(value*100, user.Discount)}р.', callback_data=f'{param}:{value}')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def sub_info_keyboard(uuid):
    return InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='🔄 Продлить подписку', callback_data=f'extend_sub:{uuid}')],
        [InlineKeyboardButton(text='📘 Инструкция', callback_data='instruction'), InlineKeyboardButton(text='🔙 Назад', callback_data='mySubs')]
    ]
)

buy_sub = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💳 Оформить подписку', callback_data='Add_Sub')]
])

async def subs_keyboard(subs: dict, page: int = 0, per_page: int = 5):
    items = list(subs.items())
    total_pages = (len(items) + per_page - 1) // per_page

    page = max(0, min(page, total_pages - 1)) if total_pages > 0 else 0

    start = page * per_page
    end = start + per_page
    page_items = items[start:end]

    keyboard = []

    for uuid, data in page_items:
        keyboard.append(
            [
                InlineKeyboardButton(text=data["email"], callback_data=f'sub:{uuid}')
            ]
        )

    if total_pages > 1:
        nav_row = []

        if page > 0:
            nav_row.append(InlineKeyboardButton(text="<", callback_data=f"subs_page:{page-1}"))

        
        nav_row.append(InlineKeyboardButton(text=f"{page+1}/{total_pages}", callback_data='noop'))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(text=f">", callback_data=f"subs_page:{page+1}"))

        keyboard.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


async def payments_keyboard(payments: list[Payments], page: int = 0, per_page: int = 5):
    total_pages = (len(payments) + per_page - 1) // per_page

    page = max(0, min(page, total_pages - 1)) if total_pages > 0 else 0

    start = page * per_page
    end = start + per_page
    page_items = payments[start:end]

    keyboard = []

    for payment in page_items:
        status_emoji = {
            "PAID": "🟢",
            "PENDING": "🟡",
            "FAILED": "🔴"
        }.get(payment.Status, "⚪")

        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} Чек #{payment.Payment_ID} — {payment.Payment_Amount}₽",
                callback_data=f"payment:{payment.Payment_ID}:{page}"
            )
        ])

    if total_pages > 1:
        nav = []

        if page > 0:
            nav.append(
                InlineKeyboardButton(text="◀️", callback_data=f"payments_page:{page-1}")
            )

        nav.append(
            InlineKeyboardButton(text=f"📄 {page+1}/{total_pages}", callback_data="noop")
        )

        if page < total_pages - 1:
            nav.append(
                InlineKeyboardButton(text="▶️", callback_data=f"payments_page:{page+1}")
            )

        keyboard.append(nav)

    return InlineKeyboardMarkup(inline_keyboard=keyboard) 

async def buy_or_back(type, months, lastMess, uuid=None, nickname=None):
    return InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='💳 Перейти к оплате', callback_data=f'{type}:{uuid}:{nickname}:{months}')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data=f'{lastMess}')]
])

async def back(lastMess):
    return InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Назад', callback_data=f'{lastMess}')]
])

async def generate_payment_link(Invoice_ID, amount):
   yookassa_payment = await yookassa.generate_payment_link(Invoice_ID, amount, f"Оплата подписки FastOne:{Invoice_ID}")
   keyboard = InlineKeyboardMarkup(
       inline_keyboard=[[InlineKeyboardButton(text='💳 Перейти к оплате', url=f'{yookassa_payment["confirmation_url"]}')]]
   )
   await rq.set_payment_status(Invoice_ID, status = None, yookassaId = yookassa_payment["yookassa_payment_id"])
   return keyboard