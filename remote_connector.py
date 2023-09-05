from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
import traceback
from typing import TYPE_CHECKING

import aiohttp
import cripy

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from cripy import Client


@asynccontextmanager
async def connect(url: str, loop: AbstractEventLoop = None, remote: bool = True) -> Client:
    try:
        client = cripy.connect(url, remote=remote, flatten_sessions=True, loop=loop or asyncio.get_event_loop())
        yield client
    except Exception:
        traceback.print_exc()
    finally:
        await client.dispose()


async def get_ws_url() -> str:
    with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:13172/json/list") as response:
            return await response.json()["webSocketDebuggerUrl"][0]


async def main() -> None:
    url = await get_ws_url()
    async with connect(url) as client:
        ...


if __name__ == "__main__":
    asyncio.run(main())
