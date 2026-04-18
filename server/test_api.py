import asyncio
from main import app
import httpx

async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        
        print("--- Fetching /tweets ---")
        resp = await ac.get("/tweets")
        print(f"Status: {resp.status_code}")
        print(resp.json())
        print("\n")
        
        print("--- Fetching /users ---")
        resp = await ac.get("/users")
        print(f"Status: {resp.status_code}")
        print(resp.json())

if __name__ == "__main__":
    asyncio.run(run())
