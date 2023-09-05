from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
import traceback
from typing import TYPE_CHECKING

import aiohttp
import cripy

try:
    import ujson as json
except ImportError:
    import json

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from cripy import Client
    from typing import cast


@asynccontextmanager
async def connect(url: str, loop: AbstractEventLoop = None, remote: bool = True) -> Client:
    try:
        client = cripy.connect(
            url,
            remote=remote,
            flatten_sessions=True,
            loop=loop or asyncio.get_event_loop(),
        )
        yield client
    except Exception:
        traceback.print_exc()
    finally:
        await client.dispose()


async def get_ws_url() -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:13172/json/list") as response:
            return await response.json()["webSocketDebuggerUrl"][0]


async def main() -> None:
    url = await get_ws_url()
    async with connect(url) as client:
        client = cast(Client, client)
        await asyncio.gather(client.Page.enable(), client.Runtime.enable(), client.Debugger.enable())


if __name__ == "__main__":
    execution_context_id = None
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
