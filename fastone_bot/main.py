import asyncio
from aiogram import Bot, Dispatcher

from fastone_bot.handlers.handlers import router
from fastone_bot.core import core
from fastone_bot.core.models import async_main
from fastone_bot.xui.xui import xui
from fastone_bot.workers.timer_worker import sub_expire_timer_worker, payment_expire_timer_worker, payments_process_timer_worker
from fastone_bot.config.config import settings



dp = Dispatcher()
dp.include_router(router)


async def main():

    bot = Bot(token=f'{settings.BOT_TOKEN}')
    core.bot = bot
    core.bot_ready.set()

    await async_main()
    await xui.start()

    asyncio.create_task(sub_expire_timer_worker())
    asyncio.create_task(payment_expire_timer_worker())
    asyncio.create_task(payments_process_timer_worker())

    await dp.start_polling(bot)


if __name__ == ("__main__"):
    asyncio.run(main())