import asyncio
from aiogram import Bot
bot: Bot | None = None
bot_ready = asyncio.Event()
polling_task = None