from fastone_bot.xui.xui_client import XUIClient
from fastone_bot.config.config import settings

xui = XUIClient(
    settings.BASE_URL,
    settings.API_TOKEN
)