from fastone_bot.core import core
import fastone_bot.core.requests as rq
from fastone_bot.xui.xui import xui
import logging

logger = logging.getLogger(__name__)

async def process_after_payment(payment_id):
    try:
        payment = await rq.get_payment(payment_id)

        if not payment:
            return
        
        user = await rq.get_user_by_userId(payment.User_ID)

        if not user:
            return
        
        tgid = user.Telegram_ID

        if payment.Payment_Plan == "NEW":
            subdata = await xui.create_subscription(payment.Payment_Nickname, payment.Payment_Months)
            await rq.create_subscription(payment.User_ID, subdata["uuid"], payment.Payment_Nickname, payment.Payment_Months)

        elif payment.Payment_Plan == "RENEW":
            await xui.renew_sub(payment.Payment_UUID, payment.Payment_Months)
            data = await xui.find_subs_by_uuids([payment.Payment_UUID])
            await rq.update_sub_expiry(payment.Payment_UUID, payment.Payment_Months, data)
    
        await core.bot_ready.wait()
        await core.bot.edit_message_text(
            chat_id=tgid,
            message_id=payment.Payment_Message_ID,
            text='Оплата получена, наслаждайтесь подпиской!\nПодписку можно найти в разделе "Мои подписки"',
        )
    except Exception:
        logger.exception(f"Ошибка при обработке после оплаты платежа {payment_id}")
        return
    
    await rq.mark_payment_as_processed(payment_id)

