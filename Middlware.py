import asyncio
from typing import Any, Awaitable, Callable, Dict, List
from aiogram import BaseMiddleware
from aiogram.types import Message

class MediaGroupMiddleware(BaseMiddleware):
    def __init__(self, latency: float = 0.5):
        self.latency = latency
        self.album_cache: Dict[str, List[Message]] = {}
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        # If the event is a button click or anything else, ignore it and let it pass through
        if not isinstance(event, Message):
            return await handler(event, data)

        # If the message is a single photo (not an album), pass it through normally
        if not event.media_group_id:
            return await handler(event, data)

        mid = event.media_group_id
        
        # If this is the first photo of the album, initialize its list cache
        if mid not in self.album_cache:
            self.album_cache[mid] = [event]
            # Wait briefly for Telegram to finish sending the rest of the album pieces
            await asyncio.sleep(self.latency)
            
            # Retrieve all gathered messages for this album and sort them by message_id
            data["album"] = self.album_cache.pop(mid)
            data["album"].sort(key=lambda msg: msg.message_id)
            
            # Trigger your handler ONCE with the full album bundle
            return await handler(event, data)
        else:
            # If the cache list already exists, append this incoming photo piece to it
            self.album_cache[mid].append(event)
            return None
