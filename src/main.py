import asyncio
import logging

import aiohttp

try:
    import ujson as json
except ImportError:
    import json

from src.CDP.remote_connector import CDPClient
from src.WebServer.dpgserver import DpgServer
from src.enums.subscriptions import EventSubscriptions

logging.basicConfig(level=logging.INFO)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("websockets").setLevel(logging.ERROR)


async def main() -> None:
    RUNNING_LOCK = asyncio.Event()

    async with aiohttp.ClientSession(json_serialize=json.dumps) as session:
        RUNNING_LOCK.set()
        DPG = asyncio.to_thread(DpgServer(RUNNING_LOCK).enter)
        CDP = CDPClient(session, RUNNING_LOCK).enter(EventSubscriptions.enable_position)
        await asyncio.gather(DPG, CDP)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Exiting...")
    except Exception as e:
        logging.exception(e)
