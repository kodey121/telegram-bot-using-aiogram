import asyncio
import logging
import sys
import aiohttp
import os

from Middlware import MediaGroupMiddleware 
from dotenv import load_dotenv
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from database import cleanup_func

# Module Router imports
from keyboard import utils_router
from commands import command_router
from support import support_router
from VideoDownloaderAiogram import handlerRouter
from photosToPdf import P2pfrouter

# i18n imports
from aiogram_i18n import I18nMiddleware
from aiogram_i18n.cores import FluentRuntimeCore
from language_manager import SQLManager

load_dotenv()

dp = Dispatcher(storage=MemoryStorage())
P2pfrouter.message.middleware(MediaGroupMiddleware())

dp.include_routers(handlerRouter, support_router, command_router, P2pfrouter, utils_router)

# Downloads and PDF process directory setup
base_dir = os.path.dirname(os.path.abspath(__file__))

downloads_path = os.path.join(base_dir, "Downloads")
photos_path = os.path.join(downloads_path, "Photos")
pdfs_path = os.path.join(downloads_path, "Pdfs")

os.makedirs(downloads_path, exist_ok=True)
os.makedirs(photos_path, exist_ok=True)
os.makedirs(pdfs_path, exist_ok=True)

# i18n Localization setup
i18n_core = FluentRuntimeCore(
    path="locales/{locale}/LC_MESSAGES"
)

i18n_middleware = I18nMiddleware(
    core=i18n_core,
    manager=SQLManager(),
    default_locale="ar"
)

# setup i18n globally on the dispatcher
i18n_middleware.setup(dispatcher=dp)

#main file rest code 
async def database_cleanup_scheduler():
    while True:
        try:
            cleanup_func() 
        except Exception as e:
            logging.error(f"Database cleanup failed: {e}")
        await asyncio.sleep(150)


async def main() -> None:
    bot_token = os.getenv("BOT_TOKEN")

    try:
        async with aiohttp.ClientSession() as check_session:
            async with check_session.get("http://127.0.0.1:8081", timeout=1.0) as resp:
                pass

        local_api_server = TelegramAPIServer.from_base("http://127.0.0.1:8081", is_local=True)
        custom_network_session = AiohttpSession(api=local_api_server)

        bot = Bot(
            token=bot_token,
            session=custom_network_session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        logging.info("SUCCESS: Routing all requests locally on port 8081 via AiohttpSession wrapper.")
        logging.info("🚀 SUCCESS: Routing requests locally on port 8081 (2GB Limit Unlocked).")
        
    except Exception as e:
        logging.warning(f"⚠️ Local server offline ({e}). Falling back to Telegram Cloud (50MB Limit)...")
        bot = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

    asyncio.create_task(database_cleanup_scheduler())

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())