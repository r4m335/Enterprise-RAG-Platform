import asyncio
import asyncpg
import sys

async def main():
    try:
        conn = await asyncpg.connect("postgresql://erag_user:erag_password@127.0.0.1:5432/erag_db")
        print("Successfully connected!")
        await conn.close()
    except Exception as e:
        print(f"Failed to connect: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
