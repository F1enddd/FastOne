import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    BASE_URL = os.getenv("XUI_BASE_URL")
    USERNAME = os.getenv("XUI_USERNAME")
    PASSWORD = os.getenv("XUI_PASSWORD")

    SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
    SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

    DB_URL = os.getenv("DATABASE_PATH")
    
    BOT_TOKEN = os.getenv("TG_BOT_TOKEN")


settings = Settings()