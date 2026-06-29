from fastapi import FastAPI

from fastone_api.payment_api import router

app = FastAPI()

app.include_router(router)