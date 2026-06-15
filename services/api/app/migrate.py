import asyncio

from .db import create_schema


if __name__ == "__main__":
    asyncio.run(create_schema())
