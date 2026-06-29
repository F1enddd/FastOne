import asyncio
from datetime import datetime, timedelta, timezone
import fastone_bot.core.core as core
from fastone_bot.payments.after_payment import process_after_payment
import fastone_bot.core.requests as rq


async def sub_expire_timer_worker():
    while True:
        await check_sub_expiring()
        await asyncio.sleep(3600)

async def payment_expire_timer_worker():
    while True:
        await expire_payments()
        await asyncio.sleep(600)

async def payments_process_timer_worker():
    while True:
        await process_paid_payments()
        await asyncio.sleep(5)


async def check_sub_expiring():
    subs = await rq.get_user_subs_for_notify()

    for sub in subs:
        user = await rq.get_user_by_userId(sub.User_ID)
        if sub.Subscription_Reminde == 0:
            await core.bot.send_message(chat_id=user.Telegram_ID, text=f'⚠️ Ваша подписка {sub.Subscription_Email} истекает в течении 3-х дней!')
            await rq.after_notify(sub.Subscription_ID)


async def expire_payments():
    now = datetime.now(timezone.utc)

    payments = await rq.get_pending_payments()

    for p in payments:
        p.Payment_Date = normalize_dt(p.Payment_Date)
        if now - p.Payment_Date > timedelta(minutes=15):
            await rq.set_payment_status(p.Payment_ID, status="FAILED")
            user = await rq.get_user_by_userId(p.User_ID)
            await core.bot.edit_message_text(
                chat_id=user.Telegram_ID,
                message_id=p.Payment_Message_ID,
                text='Счёт для оплаты просрочен❌',
            )


async def process_paid_payments():
    payments = await rq.get_unprocessed_payments()

    for p in payments:
        await process_after_payment(p.Payment_ID)


def normalize_dt(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt