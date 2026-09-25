from aiogram import Router , F
from aiogram.filters import Command,CommandStart
from aiogram.types import Message ,CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder 
from keyboard import MenuAction

from database import add_user

import unicodedata
import re

from aiogram_i18n import I18nContext

def get_clean_name(name: str, user_id: int) -> str:
    if not name:
        return f"User_{user_id}"
    
    normalized = unicodedata.normalize('NFKD', name)
    clean_text = "".join([c for c in normalized if not unicodedata.combining(c)])

    # (\u0600-\u06FF covers the main Arabic character range)

    allowed_chars_pattern = r'[^a-zA-Z0-9\u0600-\u06FF\s]'
    sanitized_name = re.sub(allowed_chars_pattern, '', clean_text).strip()
    
    #if there is no recognized characters from the library return defualt name 
    if not sanitized_name:
        return f"User_{user_id}"

    return sanitized_name

command_router=Router()

@command_router.message(Command("cancel"))
@command_router.message(F.text.casefold()=="cancel-command")
async def Cancel(message:Message,state:FSMContext,i18n:I18nContext):
    current_state= await state.get_state()
    if current_state == None:
        return
    await state.clear()
    await message.answer(text=i18n.get("cancel"))
#
@command_router.message(Command("myid"))
async def id_hundle1(msg: Message, i18n: I18nContext):
    await msg.answer(text=i18n.get("my_id", id=msg.from_user.id))

@command_router.message(Command("group_id"))
async def send_group_id(msg:Message):
    await msg.reply(text=f"{msg.chat.id}")

@command_router.message(Command("help"))
async def help_command(message:Message)->None:
    await message.answer("press /menu to start !")

#keyboard_handler

@command_router.message(CommandStart())
@command_router.message(Command("mainmenu"))
@command_router.message(Command("menu" ))
@command_router.message(Command("mainMenu"))
async def build_menu(msg: Message,i18n:I18nContext):
    # addibng the user to the data base 
    user_id = msg.from_user.id
    username=msg.from_user.full_name
    safe_name = get_clean_name(username,user_id)
    telegram_lang= msg.from_user.language_code or "ar"

    add_user(user_id=user_id, username=safe_name,language=telegram_lang)
    
    #
    
    builder = InlineKeyboardBuilder()
    button_data = MenuAction(action="open", parent_id="NULL").pack()
    
    builder.button(text=i18n.get("main-folder"), callback_data=button_data)
    builder.button(text=i18n.get("contact-support"), callback_data="support_state")
    builder.button(text=i18n.get("convert-photos2pdf"),callback_data="Photos2Pdf")
    builder.button(text=i18n.get("language"),callback_data="language")
    builder.adjust(2,3)
    await msg.reply(text=i18n.get("choose-message"), reply_markup=builder.as_markup())


@command_router.callback_query(F.data=="startMenu")
async def build_menu_callback(call:CallbackQuery,i18n:I18nContext):
    builder = InlineKeyboardBuilder()
    
    button_data = MenuAction(action="open", parent_id="NULL").pack()
    
    builder.button(text=i18n.get("main-folder"), callback_data=button_data)
    builder.button(text=i18n.get("contact-support"), callback_data="support_state")
    builder.button(text=i18n.get("convert-photos2pdf"),callback_data="Photos2Pdf")
    builder.button(text=i18n.get("language"),callback_data="language")
    builder.adjust(2,3)
    await call.message.edit_reply_markup(text=i18n.get("choose-message"), reply_markup=builder.as_markup())

@command_router.callback_query(F.data=="language")
async def cmd_change_language(call: CallbackQuery, i18n: I18nContext):
    await call.answer()
    builder = InlineKeyboardBuilder()
    builder.button(text="العربية", callback_data="set_lang:ar")
    builder.button(text="English", callback_data="set_lang:en")
    builder.adjust(2)

    await call.message.answer(
        text=i18n.get("select-language-msg"),
        reply_markup=builder.as_markup()
    )


@command_router.callback_query(F.data.startswith("set_lang:"))
async def process_language_change(call: CallbackQuery, i18n: I18nContext):
    await call.answer()
    
    new_lang = call.data.split(":")[1]
    
    await i18n.set_locale(new_lang)

    await call.message.edit_text(text=i18n.get("language-changed-msg"))
