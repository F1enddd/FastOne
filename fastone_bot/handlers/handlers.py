from aiogram import Router, F
from aiogram.filters.command import CommandStart, Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
import fastone_bot.ui.keyboards as kb
import fastone_bot.core.requests as rq
from fastone_bot.xui.xui import xui
import fastone_bot.ui.formatters as formatters

router = Router()

class NewSub(StatesGroup):
    name = State()
    months = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.first_name, message.from_user.id)

    await message.answer(
"""
<b>👋 Добро пожаловать в FastOne</b>

⚡ Быстрый, стабильный и безопасный VPN-сервис  
🔒 Защита трафика и приватность без ограничений

Выберите действие в меню ниже 👇
""",
parse_mode="HTML",
reply_markup=kb.main
)
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        payload = args[1]
        
        if payload.startswith('sub_'):
            sub_id = payload.replace('sub_','')

            subs = await xui.find_subs_by_subId(sub_id)

            if not subs:
                await message.answer("⚠️ <b>Подписка не найдена</b>", parse_mode="HTML")
                return

            expiry_time = max(c["expiryTime"] for c in subs["clients"])

            user = await rq.get_user_by_tgid(message.from_user.id)
            ext_sub = await rq.add_ext_sub(
                userId=user.User_ID,
                subUUID=subs["uuid"],
                email = subs["email"],
                expiry = expiry_time
            )
            if not ext_sub:
                await message.answer("⚠️ <b>Эта подписка уже привязана к аккаунту</b>", parse_mode="HTML")
                return
            await message.answer(f'Ваша подписка {subs["email"]} была успешно импортирована!\nВы можете найти её в разделе "Мои подписки"')

    

@router.message(F.text=='🚀 Оформить подписку')
async def add_subscribe(message: Message):
    await message.answer('Выберите на какой период оформить подписку:', reply_markup=await kb.subs_value('newsub', await rq.get_user_by_tgid(message.from_user.id)))
    
@router.callback_query(F.data=='Add_Sub')
async def add_subscribe(callback: CallbackQuery):
    
    await callback.message.edit_text('Выберите на какой период оформить подписку:', reply_markup=await kb.subs_value('newsub', await rq.get_user_by_tgid(callback.from_user.id)))
    await callback.answer()

@router.message(F.text=='👤 Личный кабинет')
async def user_personal_cabinet(message: Message):
    subs = await rq.get_user_subscriptions(message.from_user.id)
    await message.answer(
f"""
<b>👤 Личный кабинет</b>

▫️ Имя: <b>{message.from_user.first_name}</b>
▫️ ID: <code>{message.from_user.id}</code>
▫️ Подписок: <b>{len(subs)}</b>

━━━━━━━━━━━━
⚡ Управляйте своими подписками в разделе "Мои подписки"
""",
parse_mode="HTML"
)

@router.message(F.text=='ℹ️ Информация')
async def information(message: Message):
    file = FSInputFile('/root/FastOne/fastone_bot/docs/Публичная оферта FastOne.docx')
    await message.answer('Информация:\n\nТелеграм: @F1enddd\nПочта: dsus26@mail.ru\nТел: +79221004076')
    await message.answer_document(document=file, caption='Ознакомиться с публичной офертой можно здесь:')

@router.message(F.text=='📡 Мои подписки')
async def add_subscribe(message: Message):
    uuids = await rq.get_user_subscriptions(message.from_user.id)
    subs = await xui.find_subs_by_uuids(uuids)
    
    if not subs:
        await message.answer(
"""
<b>📡 У вас пока нет подписок</b>

Создайте первую подписку, чтобы начать использовать VPN
""",reply_markup=kb.buy_sub, parse_mode="HTML")
        return
    
    await message.answer(
"""
<b>📡 Ваши подписки</b>

Нажмите на подписку, чтобы открыть управление:
• статистика
• ссылка
• продление

👇
""", reply_markup=await kb.subs_keyboard(subs), parse_mode="HTML")

@router.callback_query(F.data.startswith("subs_page:"))
async def change_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])

    subs = await rq.get_user_subscriptions(callback.from_user.id)
    subs_data = await xui.find_subs_by_uuids(subs)

    keyb = await kb.subs_keyboard(subs_data, page)

    await callback.message.edit_reply_markup(reply_markup=keyb)
    await callback.answer()

@router.callback_query(F.data=='mySubs')
async def add_subscribe(callback: CallbackQuery):
    uuids = await rq.get_user_subscriptions(callback.from_user.id)
    subs = await xui.find_subs_by_uuids(uuids)
    await callback.answer()
    if not subs:
        await callback.message.edit_text("У вас нет подписок", reply_markup=kb.buy_sub)
        return
    
    await callback.message.edit_text("Ваши подписки:", reply_markup=await kb.subs_keyboard(subs))

@router.message(F.text=='💳 Платежи')
async def add_subscribe(message: Message):
    payments = await rq.get_payments_list_by_tgid(message.from_user.id)
    await message.answer(
"""
<b>💳 История платежей</b>

Здесь отображаются все ваши счета:
• 🟡 — ожидает оплату  
• 🟢 — оплачено  
• 🔴 — истёк срок оплаты

Выберите счёт для подробностей 👇
""",
reply_markup=await kb.payments_keyboard(payments),
parse_mode="HTML"
)
    

@router.callback_query(F.data.startswith("payment:"))
async def payment_info(callback: CallbackQuery):
    payment_id = int(callback.data.split(":")[1])
    page = int(callback.data.split(":")[2])

    payment = await rq.get_payment(payment_id)

    text = f"""
<b>💳 Чек #{payment.Payment_ID}</b>

━━━━━━━━━━━━
💰 <b>Сумма:</b> {payment.Payment_Amount}₽
📦 <b>Тип:</b> {payment.Payment_Plan}
📆 <b>Месяцев:</b> {payment.Payment_Months}

📌 <b>Статус:</b> {payment.Status}
🕒 <b>Создан:</b> {payment.Payment_Date:%d.%m.%Y %H:%M}

{f"✅ <b>Оплачен:</b> {payment.Payment_Paid:%d.%m.%Y %H:%M}" if payment.Payment_Paid else ""}
━━━━━━━━━━━━
"""

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=await kb.back(f'payments_page:{page}'))

    
@router.callback_query(F.data.startswith("payments_page:"))
async def change_page(callback: CallbackQuery):
    page = int(callback.data.split(":")[1])

    payments = await rq.get_payments_list_by_tgid(callback.from_user.id)

    keyb = await kb.payments_keyboard(payments, page)

    await callback.message.edit_text(
"""
<b>💳 История платежей</b>

Здесь отображаются все ваши счета:
• 🟡 — ожидает оплату  
• 🟢 — оплачено  
• 🔴 — истёк срок оплаты

Выберите счёт для подробностей 👇
""", reply_markup=keyb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("extend_sub"))
async def add_subscribe(callback: CallbackQuery):

    uuid = callback.data.split(":")[1]
    await callback.answer('')
    uuids = await rq.get_user_subscriptions(callback.from_user.id)
    subs = await xui.find_subs_by_uuids(uuids)
    sub = subs.get(uuid)

    if not sub:
        await callback.message.edit_text("⚠️ <b>Подписка не найдена</b>", parse_mode="HTML")
        return

    sub_name = sub["email"]

    await callback.message.edit_text(
f"""
<b>🔄 Продление подписки</b>

📛 <b>Название:</b> {sub_name}

Выберите срок продления 👇
""",
parse_mode="HTML",
reply_markup=await kb.subs_value(
    f'renew:{uuid}',
    await rq.get_user_by_tgid(callback.from_user.id)))



@router.callback_query(F.data.startswith("sub:"))
async def sub_menu(callback: CallbackQuery):
    uuid = callback.data.split(":")[1]

    uuids = await rq.get_user_subscriptions(callback.from_user.id)
    subs = await xui.find_subs_by_uuids(uuids)
    sub = subs.get(uuid)
    if not sub:
        await callback.message.edit_text("Подписка не найдена", show_alert=True)
        return
    
    clients = sub["clients"]

    total_up = sum(c["up"] for c in clients)
    total_down = sum(c["down"] for c in clients)
    expiry_ms = max(c.get("expiryTime", 0) for c in clients)
    subID = clients[0].get("subId")

    text = f"""
<b>📡 Подписка</b>

━━━━━━━━━━━━
📛 <b>Имя:</b> {sub['email']}
🆔 <b>UUID:</b> <code>{uuid}</code>

📊 <b>Серверов:</b> {len(clients)}
📤 <b>Отдано:</b> {formatters.format_bytes(total_up)}
📥 <b>Получено:</b> {formatters.format_bytes(total_down)}

⏳ <b>Окончание:</b> {formatters.format_expiry(expiry_ms)}
⌛ <b>Осталось:</b> {formatters.format_remaining(expiry_ms)}

🔗 <b>Ссылка:</b>
<code>https://sub.fastonevpn.ru/sub/{subID}</code>
"""
    await callback.answer()

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=await kb.sub_info_keyboard(uuid))

@router.callback_query(F.data=="instruction")
async def sub_instruction(callback: CallbackQuery):
    text = """
<b>📲 Инструкция по подключению VPN</b>

<b>1. Установите приложение</b>

<b>📱 Android:</b>
• Happ (рекомендуется)
• V2RayNG
• Clash Meta for Android

<b>📱 iPhone (iOS):</b>
• Shadowrocket (лучший вариант)
• Happ
• FoXray / Streisand

<b>💻 Windows:</b>
• Happ
• v2rayN

<b>💻 macOS:</b>
• V2RayU / Clash Verge

<b>2. Получите ссылку</b>

Перейдите в:
<b>Мои подписки → выбрать → “Скопировать ссылку”</b>


<b>3. Добавьте подписку</b>

<b>📱 Happ:</b>
• Скопируйте ссылку
• Выберите “Из буфера”
• Вставьте ссылку

<b>🍏 Shadowrocket:</b>
• Subscriptions → Add Subscription
• Вставьте ссылку
• Нажмите Download

<b>💻 v2rayN:</b>
• Subscription group → Add
• Вставьте ссылку
• Update

<b>4. Подключение</b>

• Выберите сервер
• Нажмите “Connect”

<b>⚠️ Важно:</b>
• Ссылка обновляется автоматически
• Нажимайте “Update”, если сервер не работает
• Не передавайте ссылку третьим лицам
    """

    await callback.message.edit_text(text=text, parse_mode="HTML")


@router.callback_query(F.data.startswith('renew:'))
async def buy_month_subs(callback: CallbackQuery):
    months = int(callback.data.split(":")[2])
    uuid = callback.data.split(":")[1]

    uuids = await rq.get_user_subscriptions(callback.from_user.id)
    subs = await xui.find_subs_by_uuids(uuids)
    sub = subs.get(uuid)

    if not sub:
        await callback.message.edit_text("⚠️ <b>Подписка не найдена</b>", parse_mode="HTML")
        return

    sub_name = sub["email"]
    user = await rq.get_user_by_tgid(callback.from_user.id)
    userDisc = user.Discount
    await callback.answer()
    await callback.message.edit_text(
f"""
<b>➕ Продление подписки</b>

📛 <b>Название:</b> {sub_name}
📝 <b>Описание:</b> Продление подписки VPN-сервиса FastOne на {months} мес.
📆 <b>Срок:</b> {months} мес.
💰 <b>Стоимость:</b> {formatters.format_cost(months*100, userDisc)}₽

━━━━━━━━━━━━
⚡ После оплаты подписка будет продлена автоматически
""",
parse_mode="HTML",
reply_markup=await kb.buy_or_back("pay_renew", months, f'extend_sub:{uuid}', uuid))



@router.callback_query(F.data.startswith('newsub:'))
async def buy_month_subs(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split(":")[1])

    await state.update_data(months = months)
    
    await state.set_state(NewSub.name)

    await callback.message.edit_text("Введите название подписки: ")

    

    return

@router.message(NewSub.name)
async def get_sub_name(message: Message, state: FSMContext):
    if not message or not message.text or len(message.text) < 3:
        await message.answer(text='Название неверное или слишком короткое')
        return
    sub_name = message.text
    await state.update_data(sub_name=sub_name)

    exists = await xui.subs_name_exist(sub_name)
    if exists:
        await message.answer(text='Подписка с таким названием уже существует')
        return
    
    data = await state.get_data()

    months = data["months"]

    user = await rq.get_user_by_tgid(message.from_user.id)
    userDisc = user.Discount

    await message.answer(
f"""
<b>➕ Создание подписки</b>

📛 <b>Название:</b> {sub_name}
📝 <b>Описание:</b> Подписка VPN-сервиса FastOne на {months} мес.
📆 <b>Срок:</b> {months} мес.
💰 <b>Стоимость:</b> {formatters.format_cost(months*100, userDisc)}₽

━━━━━━━━━━━━
⚡ После оплаты подписка будет активирована автоматически
""",
parse_mode="HTML",
reply_markup=await kb.buy_or_back('pay_new', months, 'Add_Sub', nickname=sub_name)
)


@router.callback_query(F.data.startswith('pay_renew'))
async def buy_month_subs(callback: CallbackQuery):

    uuid = callback.data.split(":")[1]
    months = int(callback.data.split(":")[3])

    user = await rq.get_user_by_tgid(callback.from_user.id) 
    payment = await rq.create_payment(user.User_ID, formatters.format_cost(months*100, user.Discount), "RENEW", months, uuid)
     
    msg = await callback.message.edit_text(
f"""
<b>💳 Счёт создан</b>

🧾 №: <b>{payment.Payment_ID}</b>
💰 Сумма: <b>{payment.Payment_Amount}₽</b>

Нажмите кнопку ниже для оплаты 👇
""", reply_markup=await kb.generate_payment_link(payment.Payment_ID, payment.Payment_Amount), parse_mode="HTML")
    await rq.add_payment_message_id(msg.message_id, payment.Payment_ID)
    await callback.answer()



    
    


    
@router.callback_query(F.data.startswith('pay_new'))
async def buy_month_subs(callback: CallbackQuery, state: FSMContext):

    months = int(callback.data.split(":")[3])
    nickname = callback.data.split(":")[2]

    user = await rq.get_user_by_tgid(callback.from_user.id) 
    payment = await rq.create_payment(user.User_ID, formatters.format_cost(months*100, user.Discount), "NEW", months, nickname=nickname)
    await callback.answer()

    msg = await callback.message.edit_text(
f"""
<b>💳 Счёт создан</b>

🧾 №: <b>{payment.Payment_ID}</b>
💰 Сумма: <b>{payment.Payment_Amount}₽</b>

Нажмите кнопку ниже для оплаты 👇
""", reply_markup=await kb.generate_payment_link(payment.Payment_ID, payment.Payment_Amount), parse_mode="HTML")
    
    await rq.add_payment_message_id(msg.message_id, payment.Payment_ID)
    await callback.answer()






