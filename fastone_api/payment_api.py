from fastapi import FastAPI, Form, HTTPException, Request, APIRouter
from fastone_bot.core import requests as rq
import asyncio

router = APIRouter()


@router.get("/")
async def root():
    return {"status": "ok"}

@router.post("/yookassa/webhook")
async def yookassa_webhook(request: Request):

    payload = await request.json()

    print("CALLBACK YOOKASSA")
    
    
    if payload.get("event") != "payment.succeeded":
        return {"status":"ignored"}
    
    print(f'Оплата подписки FastOne сумма:{payload["object"]["amount"]["value"]}')
    
    obj = payload["object"]

    payment_id = int(obj["metadata"]["payment_id"])
    yookassa_payment_id = obj["id"]
    db_payment = await rq.get_payment(payment_id)

    if not db_payment:
        print("PAYMENT NOT FOUND:", payment_id)
        return {"status": "not_found"}

    if db_payment.Payment_yookassa_ID != yookassa_payment_id:
        return {"status":"invalid"}
    
    if db_payment.Status == "PAID":
        return {"status": "already_paid"}

    await rq.set_payment_status(payment_id, status="PAID")

    return {"status":"ok"}
