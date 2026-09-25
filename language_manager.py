from aiogram_i18n.managers import BaseManager
from aiogram.types import User
from database import get_user_language ,update_user_language

class SQLManager(BaseManager):

    async def get_locale(self, event_from_user: User) -> str:
        if not event_from_user:
            return "ar"
        
        return get_user_language(event_from_user.id)

    async def set_locale(self, locale: str, event_from_user: User) -> None:
        if event_from_user:
            
            update_user_language(event_from_user.id, locale)