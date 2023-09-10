from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Iterable

import cripy

try:
    import ujson as json
except ImportError:
    import json

from ..enums.subscriptions import EventSubscriptions
from ..types.iterable_queue import Queue
from ..types.position import Position


if TYPE_CHECKING:
    from asyncio import Event
    from typing import Any
    from cripy import Client
    from aiohttp import ClientSession


class CDPClient:
    client: Client
    context_id: int

    def __init__(self, client_session: ClientSession, running: Event):
        self.logger = logging.getLogger(__name__)
        self.session = client_session
        self.running = running
        self.nodes: [Queue[Position]] = Queue()

    async def get_ws_url(self) -> str:
        async with self.session.get("http://localhost:13172/json/list") as response:
            if response.status != 200:
                self.logger.error(f"Failed to get websocket url: {response.status}\n{response.reason}")
            data = await response.json()
            self.logger.info(f"WS URL found: {data[0]['webSocketDebuggerUrl']}")
            return data[0]["webSocketDebuggerUrl"]

    async def entry(self, subscription: EventSubscriptions | Iterable[EventSubscriptions]) -> None:
        if not (url := await self.get_ws_url()):
            return
        self.running.set()
        try:
            self.client = await cripy.connect(url, remote=False, flatten_sessions=True)
        except Exception as e:
            self.logger.exception(e)

        self.client.Runtime.bindingCalled(self.on_binding_called)
        self.client.Debugger.scriptParsed(self.on_script_parsed)
        await asyncio.gather(
            self.client.Page.enable(),
            self.client.Runtime.enable(),
            self.client.Debugger.enable(),
        )
        if isinstance(subscription, Iterable):
            for event in subscription:
                await self.send_app_command(event)
        else:
            await self.send_app_command(subscription)

        while not self.client.closed and self.running.is_set():
            await asyncio.sleep(30)
            self.running.clear()
        await self.close()

    async def close(self):
        if self.client:
            await self.client.dispose()
        for item in self.nodes:
            self.logger.info(item)

    async def on_binding_called(self, payload: dict[str, Any]) -> None:
        payload = json.loads(payload["payload"])
        if payload["type"] != "position":
            return
        self.nodes.put_nowait(Position(*payload["data"]))

    async def on_script_parsed(self, payload: dict[str, Any]) -> None:
        self.logger.debug(f"Script parsed: {payload}")
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
