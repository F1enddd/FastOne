from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import BigInteger, ForeignKey, DateTime
from datetime import datetime, timezone
from fastone_bot.config.config import settings

DB_URL = settings.DB_URL

engine = create_async_engine(url=DB_URL)
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Users(Base):
    __tablename__ = 'USER'

    User_ID: Mapped[int] = mapped_column(primary_key=True)
    User_Name: Mapped[str] = mapped_column()
    Telegram_ID = mapped_column(BigInteger)
    Discount: Mapped[int] = mapped_column()
    

class Subscriptions(Base):
    __tablename__ = 'SUBSCRIPTION'

    Subscription_ID: Mapped[int] = mapped_column(primary_key=True)
    User_ID: Mapped[int] = mapped_column(ForeignKey('USER.User_ID'))
    Subscription_UUID: Mapped[str] = mapped_column()
    Subscription_Email: Mapped[str] = mapped_column()
    Subscription_Expiry: Mapped[int] = mapped_column()

    # 0 / 1 
    Subscription_Reminde: Mapped[int] = mapped_column(default=0)

class Payments(Base):
    __tablename__ = "PAYMENT"

    Payment_ID: Mapped[int] = mapped_column(primary_key=True)

    User_ID: Mapped[int] = mapped_column(
        ForeignKey("USER.User_ID")
    )

    Payment_Date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    Payment_Amount: Mapped[int] = mapped_column(nullable=False)

    # PENDING / PAID / FAILED
    Status: Mapped[str] = mapped_column()

    # RENEW / NEW
    Payment_Plan: Mapped[str] = mapped_column()

    Payment_UUID: Mapped[str | None] = mapped_column()
    Payment_Nickname: Mapped[str | None] = mapped_column()

    Payment_Months: Mapped[int] = mapped_column()

    Payment_Paid: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    Payment_Message_ID: Mapped[str | None] = mapped_column() 

    Payment_yookassa_ID: Mapped[str | None] = mapped_column()

    Payment_Processed: Mapped[int] = mapped_column(default=0)

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
