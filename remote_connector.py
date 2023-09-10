from __future__ import annotations

import asyncio
from contextlib import suppress
from enum import Enum
import logging
from typing import TYPE_CHECKING

import aiohttp
import cripy

try:
    import ujson as json
except ImportError:
    import json

if TYPE_CHECKING:
    from cripy import Client
    from typing import Any, Literal, LiteralString

logging.basicConfig(level=logging.INFO)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)


class EventSubscriptions(Enum):
    enable_map_data_relay = "enableMapDataRelay"  # enables all events
    enable_position = "enablePosition"  # sends a position update every 100ms with [x, y, z, heading]
    enable_players = "enablePlayers"  # sends a players event back every 100ms with [[x, y, z], ...]
    enable_peds = "enablePeds"  # sends a peds event back every 400ms with [[x, y, z], ...]
    enable_blips = "enableBlips"  # sends a blips event every 30s with [[x, y, z, sprite, colour, alpha, type], ...]
    enable_chat = "enableChat"  # sends a chat event when a chat message is received, data may depend on message


async def get_ws_url() -> str:
    async with aiohttp.ClientSession(json_serialize=json.dumps) as session:
        async with session.get("http://localhost:13172/json/list") as response:
            if response.status != 200:
                logging.error(f"Failed to get websocket url: {response.status}\n{response.reason}")
            data = await response.json()
            return data[0]["webSocketDebuggerUrl"]


class CDPClient:
    client: Client
    context_id: int

    def __init__(self, url: LiteralString):
        self.url = url
        self.nodes: dict[Literal["X", "Y", "Z", "Heading"], list[float]] = {"X": [], "Y": [], "Z": [], "Heading": []}

    async def entry(self) -> None:
        try:
            self.client = await cripy.connect(self.url, remote=False, flatten_sessions=True)
        except Exception as e:
            logging.exception(e)

        self.client.Runtime.bindingCalled(self.on_binding_called)
        self.client.Debugger.scriptParsed(self.on_script_parsed)
        await asyncio.gather(
            self.client.Page.enable(),
            self.client.Runtime.enable(),
            self.client.Debugger.enable(),
        )
        await self.send_app_command(EventSubscriptions.enable_position)

        while not self.client.closed:
            await asyncio.sleep(1)
        await self.close()

    async def close(self):
        if self.client:
            await self.client.dispose()

    async def on_binding_called(self, payload: dict[str, Any]) -> None:
        payload = json.loads(payload["payload"])
        if payload["type"] != "position":
            return
        for i, key in enumerate(self.nodes):
            self.nodes[key].append(payload["data"][i])

    async def on_script_parsed(self, payload: dict[str, Any]) -> None:
        logging.debug(f"Script parsed: {payload}")
        if "nui/main.js" not in payload.get("url"):
            return
        self.context_id = payload.get("executionContextId")

        await self.client.Runtime.addBinding("sendDevtools", self.context_id)
        await self.client.Runtime.evaluate(
            expression="recvData('message', JSON.stringify({a: 'b'}))", contextId=self.context_id, awaitPromise=True
        )

    async def send_app_command(self, event: EventSubscriptions) -> Any:
        return await self.client.Runtime.evaluate(
            expression=f"recvData('{event.value}')", contextId=self.context_id, awaitPromise=True
        )


async def main() -> None:
    url = await get_ws_url()
    logging.info(f"Websocket URL found: {url}")
    await CDPClient(url).entry()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(main())
