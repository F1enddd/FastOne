import uuid
import aiohttp
from fastone_bot.config.config import settings 

SHOP_ID = settings.SHOP_ID
SECRET_KEY = settings.SECRET_KEY

API_URL = 'https://api.yookassa.ru/v3/payments'

async def generate_payment_link(payment_id: int, amount: int, description: str):
    payload = {
        "amount": {
            "value": f'{amount:.2f}',
            "currency": "RUB"
        },
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": "https://t.me/FastOneVPN_bot"
        },
        "description": description,
        "metadata": {
            "payment_id": str(payment_id)
        }
    }

    headers = {
        "Idempotence-Key": str(uuid.uuid4())
    }

    async with aiohttp.ClientSession(
        auth = aiohttp.BasicAuth(
            login=SHOP_ID,
            password=SECRET_KEY
        )
    ) as session:
        async with session.post(
            API_URL,
            json=payload,
            headers=headers
        ) as response:
            
            if response.status not in (200, 201):
                text = await response.text()
                raise Exception(
                    f"yookassa error {response.status}: {text}"
                )
            
            data = await response.json()
    

    return {
        "yookassa_payment_id": data["id"],
        "confirmation_url": data["confirmation"]["confirmation_url"]
        }