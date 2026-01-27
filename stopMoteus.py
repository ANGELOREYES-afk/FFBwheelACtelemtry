import moteus
import asyncio

async def main():
    c = moteus.Controller()
    await c.set_stop()

if __name__ == "__main__":
    asyncio.run(main())