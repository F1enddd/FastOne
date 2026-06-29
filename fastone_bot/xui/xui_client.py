import aiohttp
import asyncio
from datetime import timezone, datetime, timedelta
import uuid as uuid_lib
import json


class XUIClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.session = None

    async def login(self):
        async with self.session.post(
            f"{self.base_url}/login",
            data={
                "username": self.username,
                "password": self.password
            }
        ) as resp:
            text = await resp.text()
            print("LOGIN:", resp.status, text)
    
    async def request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"

        for attempt in range(2):
            if self.session is None:
                await self.start()

            async with self.session.request(method, url, **kwargs) as resp:
                text = await resp.text()

                if resp.status in (401, 403, 404) and attempt == 0:
                    await self.login()
                    continue

                if resp.status >= 400:
                    raise Exception(
                        f"XUI HTTP {resp.status}: {text[:500]}"
                    )

                try:
                    return json.loads(text)
                except Exception:
                    raise Exception(
                        f"XUI returned non-json: {text[:500]}"
                    )

        raise Exception("Request failed after re-login")


    async def start(self):
        jar = aiohttp.CookieJar(unsafe=True)
        self.session = aiohttp.ClientSession(cookie_jar=jar)

        await self.login()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()

    async def get_subs(self):
        print(self.base_url)
        return await self.request("GET", "/panel/api/inbounds/list")
        
    async def find_subs_by_uuids(self, uuids: list[str]):
        uuids = set(uuids)
        grouped = {}

        data = await self.get_subs()

        for inbound in data["obj"]:
            for client in inbound["clientStats"]:

                uuid = client["uuid"]

                if uuid not in uuids:
                    continue

                if uuid not in grouped:
                    grouped[uuid] = {
                        "email": client["email"].split(" - ")[0],
                        "uuid": uuid,
                        "clients": []
                    }

                grouped[uuid]["clients"].append({
                **client,
                "inboundId": inbound["id"]
                })

        return grouped

    async def subs_name_exist(self, sub_name):
        subs = await self.get_subs()

        for inbound in subs['obj']:
            for client in inbound['clientStats']:

                email = client['email']

                if email == f'{sub_name} - #1':
                    return True
                
        return False
    

    async def add_client(self, inbound_id, client: dict):
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [client]
            })
        }

        return await self.request(
            "POST",
            "/panel/api/inbounds/addClient",
            json=payload
        )


    async def update_client(self, inbound_id: int, client: dict, uuid):
        payload = {
            "id": inbound_id,
            "settings": json.dumps({
                "clients": [client]
            })
        }

        return await self.request(
            "POST",
            f"/panel/api/inbounds/updateClient/{uuid}",
            json=payload
        )
    
    async def create_subscription(self, username: str, months: int):
        user_uuid = str(uuid_lib.uuid4())

        expire_time = int((
            datetime.now(timezone.utc) + timedelta(days=30 * months)
        ).timestamp() * 1000)

        subscription_id = str(uuid_lib.uuid4())

        base_client = {
            "id": user_uuid,
            "enable": True,
            "expiryTime": expire_time,
            "flow": "",
            "subId": subscription_id
        }

        client_1 = {
            **base_client,
            "email": f'{username} - #1'
        }
        
        client_2 = {
            **base_client,
            "email": f'{username} - #2'
        }

        r1 = await self.add_client(1, client_1)
        print("ADD1", r1)
        r2 = await self.add_client(2, client_2)
        print("ADD2", r2)


        return {
            "uuid": user_uuid,
            "subId": subscription_id,
            "expire": expire_time
        }
    
    async def renew_sub(self, uuid, months):
        data = await self.find_subs_by_uuids([uuid])
        clients = data.get(uuid, {}).get("clients", [])

        cur_expire = max(c.get("expiryTime", 0) for c in clients)

        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)

        base_time = max(cur_expire, now_ms)

        add_ms = int(timedelta(days=30 * months).total_seconds() * 1000)

        expire_time = base_time + add_ms

        for client in clients:
            updated = {
                "id": uuid,
                "email": client["email"],
                "enable": True,
                "expiryTime": expire_time,
                "flow": "",
                "subId": client.get("subId")
            }

            r = await self.update_client(client["inboundId"], updated, uuid)
            print(r)

    async def find_subs_by_subId(self, subId):
        data = await self.get_subs()
        for inbound in data["obj"]:
            for client in inbound["clientStats"]:
                if client.get("subId") == subId:
                    
                    uuid = client["uuid"]

                    subs = await self.find_subs_by_uuids([uuid])
                    return subs.get(uuid)
        
        return None
