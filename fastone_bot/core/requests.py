from datetime import datetime, timezone, timedelta
from fastone_bot.core.models import async_session
from fastone_bot.core.models import Users, Subscriptions, Payments
from sqlalchemy import select, update, delete


async def set_user(username, tg_id):
    async with async_session() as session:
        user = await session.scalar(select(Users).where(Users.Telegram_ID == tg_id))

        if not user:
            session.add(Users(User_Name=username, Telegram_ID=tg_id, Discount=0))
            await session.commit()
            
async def get_user_by_tgid(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(Users).where(Users.Telegram_ID == tg_id))

        if not user:
            return None
        return user

async def get_user_subscriptions(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(Users).where(Users.Telegram_ID == tg_id))

        if not user:
            return []
        
        Subs = await session.scalars(select(Subscriptions).where(Subscriptions.User_ID == user.User_ID))
        uuids = [sub.Subscription_UUID for sub in Subs]
        return uuids
        
async def create_payment(user_id, amount, plan, months, uuid = None, nickname = None):
    async with async_session() as session:
        payment = Payments(
            User_ID = user_id,
            Payment_Amount = amount,
            Status = 'PENDING',
            Payment_Plan = plan,
            Payment_Months = months,
            Payment_Paid = None,
            Payment_UUID = uuid,
            Payment_Nickname = nickname
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)

        return payment

async def get_payment(payment_id):
    async with async_session() as session:
        payment = await session.scalar(select(Payments).where(Payments.Payment_ID == payment_id))
        return payment
    

async def create_subscription(user_id, uuid, email, months):
    async with async_session() as session:
        expity = int((datetime.now(timezone.utc) + timedelta(days=30 * months)).timestamp() * 1000)
        subscription = Subscriptions(
            User_ID = user_id,
            Subscription_UUID = uuid,
            Subscription_Email = email,
            Subscription_Expiry = expity
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)

        return subscription

async def get_user_subs_for_notify():
    async with async_session() as session:
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        in_3_days = now_ms + 3*24*60*60*1000
        subs = await session.scalars(select(Subscriptions).where(Subscriptions.Subscription_Expiry.between(now_ms, in_3_days)))
        return subs.all()

async def get_user_by_userId(userId):
    async with async_session() as session:
        user = await session.scalar(select(Users).where(Users.User_ID == userId))
        return user
    
async def after_notify(Subscription_Id):
    async with async_session() as session:
        subscription = await session.scalar(select(Subscriptions).where(Subscriptions.Subscription_ID == Subscription_Id))
        if not subscription:
            return
        subscription.Subscription_Reminde = 1
        await session.commit()
        return True
    
async def add_ext_sub(userId, subUUID, email, expiry):
    async with async_session() as session:
        ext_sub = await session.scalar(select(Subscriptions).where(Subscriptions.Subscription_UUID == subUUID))

        if ext_sub: 
            return None
        
        sub = Subscriptions(
            User_ID = userId,
            Subscription_UUID = subUUID,
            Subscription_Email = email,
            Subscription_Expiry = expiry
        )

        session.add(sub)
        await session.commit()
        return sub

async def update_sub_expiry(uuid, months, data):
    async with async_session() as session:
        sub = await session.scalar(select(Subscriptions).where(Subscriptions.Subscription_UUID == uuid))

        if not sub:
            return

        clients = data.get(uuid, {}).get("clients", [])

        cur_expire = max((c.get("expiryTime", 0) for c in clients), default=0)

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        base_time = max(cur_expire, now_ms)

        add_ms = int(timedelta(days=30 * months).total_seconds() * 1000)

        sub.Subscription_Expiry = base_time + add_ms
        sub.Subscription_Reminde = 0

        await session.commit()

        return

async def get_payments_list_by_tgid(tgid):
    async with async_session() as session:
        user = await get_user_by_tgid(tgid)
        userId = user.User_ID
        payments = await session.scalars(select(Payments).where(Payments.User_ID == userId))

        return payments.all()
    
async def get_pending_payments():
    async with async_session() as session:
        payments = await session.scalars(select(Payments).where(Payments.Status == "PENDING"))

        return payments.all()
    
async def set_payment_status(paymentId, status = None, yookassaId = None):
    async with async_session() as session:
        payment = await session.scalar(select(Payments).where(Payments.Payment_ID == paymentId))
        if not payment:
            return False
        if status:
            if payment.Status != "PENDING" and status == "FAILED":
               return False
            if status == "PAID":
                payment.Payment_Paid = datetime.now()
            payment.Status = status
        if yookassaId:
            payment.Payment_yookassa_ID = yookassaId

        await session.commit()
        
        
        return True
    
async def add_payment_message_id(msg, paymentId):
    async with async_session() as session:
        payment = await session.scalar(select(Payments).where(Payments.Payment_ID == paymentId))
        if not payment:
            return
        payment.Payment_Message_ID = msg

        await session.commit()

        return True


async def get_unprocessed_payments():
    async with async_session() as session:
        result = await session.scalars(select(Payments).where(Payments.Payment_Processed == 0, Payments.Status == "PAID"))

        return result.all()
    
async def mark_payment_as_processed(paymentId):
    async with async_session() as session:
        payment = await session.scalar(select(Payments).where(Payments.Payment_ID == paymentId))

        if not payment:
            return False
        
        payment.Payment_Processed = 1
        await session.commit()

        return True