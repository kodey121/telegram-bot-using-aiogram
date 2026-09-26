import os
import asyncio
from random import randint
from dotenv import load_dotenv

from aiogram import Router, F 
from aiogram.types import Message, KeyboardButton, CallbackQuery, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram_i18n import I18nContext

import aiohttp
import logging
from pydantic import ValidationError
from aiogram.exceptions import TelegramBadRequest

import database 
import config

load_dotenv()

owner_id = os.getenv('OWNER_ID')
RONWER_ID = int(owner_id) if owner_id else 0

utils_router = Router()

class MenuAction(CallbackData, prefix="menu"):
    action: str
    parent_id: str 

class AdminAction(CallbackData, prefix="admin"):
    admin_name: str
    admin_id: str 

class create_button(StatesGroup):
    get_name = State()

class upload_file(StatesGroup):
    get_file_id = State()
    finish = State()

class add_admin(StatesGroup):
    get_admin_id = State()

class add_support_group(StatesGroup):
    get_group_id = State()

class get_the_new_name(StatesGroup):
    get_the_name = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast_msg = State()


@utils_router.message(F.text == "Finish✅")
async def finishing_handling(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(text="Buttons:", reply_markup=ReplyKeyboardRemove())

@utils_router.message(F.text == "✅Finish✅")
async def finishing_handling(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(reply_markup=ReplyKeyboardRemove())

@utils_router.callback_query(MenuAction.filter(F.action == "send_admin_list"))
async def handle_send_admin_list(call: CallbackQuery, i18n: I18nContext):
    admin_data = database.get_admin_info()
    admin_list = []
    for admin_id, admin_name in admin_data:
        admin_list.append(f"{admin_name}:{admin_id}")

    response_text = "\n".join(admin_list) if admin_list else i18n.get("no_admin_yet_message")

    await call.message.answer(text=f"{i18n.get('show_admins_message')}\n{response_text}")
    await call.answer()


@utils_router.callback_query(MenuAction.filter(F.action == "back_to_main"))
async def back_to_main_handle(call: CallbackQuery, i18n: I18nContext):
    mark_up = build_dynamic_menu(parent_id="NULL", user_id=call.from_user.id, i18n=i18n)
    await call.message.edit_reply_markup(reply_markup=mark_up)


@utils_router.callback_query(MenuAction.filter(F.action == "select_supp_group"))
async def selecting_groups_handling(call: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await call.message.reply(text=i18n.get("select_support_group_message"))
    await state.set_state(add_support_group.get_group_id) 


@utils_router.message(add_support_group.get_group_id)
async def handle_group_selecting_state(msg: Message, state: FSMContext, i18n: I18nContext):
    group_id = msg.text
    config.write_settings("supprot_group", group_id)
    await msg.reply(text=f"{i18n.get('updated-group-support-message')} {group_id}")
    await state.clear()


@utils_router.callback_query(MenuAction.filter(F.action == "add_admin"))
async def add_admin_handling(call: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await call.message.answer(text=i18n.get("ask-about-user-id-tomake-admin"))
    await state.set_state(add_admin.get_admin_id)


@utils_router.callback_query(MenuAction.filter(F.action == "remove_admin_list"))
async def remove_admin_building_menu(call: CallbackQuery, callback_data: MenuAction, i18n: I18nContext):
    builder = InlineKeyboardBuilder()
    admin_list = database.get_admin_info()
    
    if not admin_list:
        await call.message.answer(text=i18n.get('no_admin_yet_message'))
        parent_id = callback_data.parent_id
        user_id = call.from_user.id
        
        mark_up = build_dynamic_menu(parent_id, user_id, i18n=i18n)
        await call.message.answer(text=f"folder: {parent_id}", reply_markup=mark_up)
    else:
        for admin_id, admin_name in admin_list:
            builder.button(
                text=f"{admin_name}:{admin_id}",
                callback_data=AdminAction(admin_name=f"{admin_name}", admin_id=str(admin_id)).pack()
            )
        builder.adjust(1, 2)
        await call.message.answer(text=i18n.get("select_admin_to_remove_message"), reply_markup=builder.as_markup())


@utils_router.callback_query(AdminAction.filter())
async def remove_admin_handling(call: CallbackQuery, callback_data: AdminAction, i18n: I18nContext):
    admin_name = callback_data.admin_name
    admin_id = callback_data.admin_id

    admin_ids_list = database.get_admin_ids()
    if admin_id not in admin_ids_list:
        await call.message.answer(text=f"{i18n.get('there_is_no_admmin_adminid')} {admin_name}")
    else:
        builder = InlineKeyboardBuilder()
        database.remove_admin(admin_id)
        await call.message.edit_text(text=f"{admin_name} {i18n.get('adminid_removed_message')}")
        
        admin_list = database.get_admin_info()
        for a_id, a_name in admin_list:
            builder.button(
                text=f"{a_name}:{a_id}",
                callback_data=AdminAction(admin_name=f"{a_name}", admin_id=str(a_id)).pack()
            )
        builder.adjust(1, 2)

        if len(admin_ids_list) > 1:
            await call.message.edit_reply_markup(reply_markup=builder.as_markup())


@utils_router.callback_query(MenuAction.filter(F.action == "RenameF"))
async def rename_folder_func(call: CallbackQuery, state: FSMContext, callback_data: MenuAction, i18n: I18nContext):
    await call.message.answer(i18n.get("enter_button_name_message"))
    await state.update_data(parent_id=callback_data.parent_id)
    await state.set_state(get_the_new_name.get_the_name)


@utils_router.message(get_the_new_name.get_the_name)
async def handle_the_new_name(msg: Message, state: FSMContext, i18n: I18nContext):
    new_name = msg.text
    data = await state.get_data()
    parent_id = data.get("parent_id")
    database.remame_button(new_name=new_name, parent_id=parent_id)
    await msg.reply(text=f"{i18n.get('succss_button_name_changing')}")
    await state.clear()


@utils_router.message(add_admin.get_admin_id)
async def add_admin_handling_state(msg: Message, i18n: I18nContext):
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅Finish✅"))
    admin_id = msg.text.strip()

    admin_name = f"User_{admin_id}"
    user_tag = f"ID: {admin_id}"

    try:
        admin_info = await msg.bot.get_chat(admin_id)
        admin_name = admin_info.full_name or f"Admin_{admin_id}"
        user_tag = f"@{admin_info.username}" if admin_info.username else admin_name

    except ValidationError:
        try:
            url = f"https://api.telegram.org/bot{msg.bot.token}/getChat?chat_id={admin_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    res = await resp.json()
                    if res.get("ok"):
                        data = res.get("result", {})
                        first = data.get("first_name", "")
                        last = data.get("last_name", "")
                        
                        admin_name = f"{first} {last}".strip() or f"Admin_{admin_id}"
                        username = data.get("username")
                        user_tag = f"@{username}" if username else admin_name
        except Exception as http_err:
            logging.error(f"Raw HTTP lookup failed: {http_err}")

    except (TelegramBadRequest, Exception) as e:
        logging.error(f"Failed to fetch admin info for ID {admin_id}: {e}")

    database.add_admin(admin_id, admin_name)

    await msg.answer(
        text=f"{user_tag} {i18n.get('succssfully_added_new_admin')}", 
        reply_markup=builder.as_markup()
    )


@utils_router.callback_query(MenuAction.filter(F.action == "delete_f"))
async def delete_file_handling(call: CallbackQuery, callback_data: MenuAction, i18n: I18nContext):
    parent_id = callback_data.parent_id
    if not database.get_files_ids(parent_id):
        await call.message.answer(text=i18n.get("no_lecture_to_delete_message"))
        await call.answer()
    else:
        database.remove_uploaded_file(parent_id)
        await call.message.answer(text=i18n.get("lectures_deleted_message"))
        await call.answer()


@utils_router.callback_query(MenuAction.filter(F.action == "send_flist"))
async def file_sending_info121(call: CallbackQuery, callback_data: MenuAction, i18n: I18nContext):
    parent_id = callback_data.parent_id
    ids = database.get_files_ids(parent_id)

    if not ids:
        await call.message.answer(text=i18n.get("no_lectures_message"))
    else:
        text = ""
        for file_id, doc_id, doc_name in ids:
            file_id_str = i18n.get("exact_fileid", file_id=file_id)
            file_name_str = i18n.get("exact_filename", file_name=doc_name)
            text += f"{file_id_str}, {file_name_str}\n\n"
        await call.message.answer(text=text)
        await call.answer()


@utils_router.callback_query(MenuAction.filter(F.action == "send_file"))
async def file_sending(call: CallbackQuery, callback_data: MenuAction, i18n: I18nContext):
    parent_id = callback_data.parent_id
    ids = database.get_files_ids(parent_id)

    if not ids:
        await call.message.answer(text=i18n.get("no_lectures_message"))
    else:
        for file_id, doc_id, doc_name in ids:
            caption_num = i18n.get("exact_filenum", file_num=file_id)
            caption_id = i18n.get("exact_fileid", file_id=file_id)
            try:
                await call.message.answer_document(document=doc_id, caption=caption_num)
            except Exception:
                await call.message.answer_photo(photo=doc_id, caption=caption_id)


@utils_router.callback_query(MenuAction.filter(F.action == "add"))
async def add_button(call: CallbackQuery, state: FSMContext, callback_data: MenuAction, i18n: I18nContext):
    await call.message.answer(text=i18n.get("enter_button_name_message"))
    await state.update_data(par_id=callback_data.parent_id)
    await state.set_state(create_button.get_name)


@utils_router.callback_query(MenuAction.filter(F.action == "upload"))
async def upload_hundle(call: CallbackQuery, state: FSMContext, callback_data: MenuAction, i18n: I18nContext):
    await state.update_data(parent_id=callback_data.parent_id)
    await call.message.answer(text=i18n.get("ask_upload_file_message"))
    await state.set_state(upload_file.get_file_id)


@utils_router.callback_query(MenuAction.filter(F.action == "proadcast"))
async def ask_broadcast_message(call: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await call.message.reply(i18n.get("ask_forward_or-send_message2_proadcast"))
    await state.set_state(AdminStates.waiting_for_broadcast_msg)


@utils_router.message(AdminStates.waiting_for_broadcast_msg)
async def execute_broadcast(msg: Message, state: FSMContext, i18n: I18nContext):
    await state.clear()
    await msg.reply(i18n.get("proadcast_started_message"))
    asyncio.create_task(safe_broadcast(bot=msg.bot, admin_chat_id=msg.chat.id, broadcast_message=msg, i18n=i18n))


@utils_router.message(upload_file.get_file_id, F.photo)
@utils_router.message(upload_file.get_file_id, F.document)
async def getting_files(msg: Message, state: FSMContext, i18n: I18nContext):
    data = await state.get_data()
    parent_id = data.get("parent_id")
    try:
        doc_name = msg.document.file_name
        doc_id = msg.document.file_id
    except AttributeError:
        doc_name = f'{msg.photo[-1].file_size}:{randint(0,100)}' 
        doc_id = msg.photo[-1].file_id
    
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Done"))

    await msg.answer(text=i18n.get("wating_for_file-message"), reply_markup=builder.as_markup())
    database.upload_file(parent_id, doc_id, doc_name)
    await msg.answer(text=f"{doc_name} {i18n.get('file_uplaoded_message')}")


@utils_router.message(F.text == "✅ Done")
async def handle_stop_upload(msg: Message, state: FSMContext, i18n: I18nContext):
    data = await state.get_data()
    parent_id = data.get("parent_id")
    user_id = msg.from_user.id

    await state.clear()
    await msg.answer(text=i18n.get("upload_opreation_finished-reloading_menu"), reply_markup=ReplyKeyboardRemove())

    reply_markup = build_dynamic_menu(parent_id, user_id, i18n=i18n)
    folder_str = i18n.get("exact_folder", folder_name=str(parent_id))
    await msg.answer(text=folder_str, reply_markup=reply_markup)


@utils_router.callback_query(MenuAction.filter(F.action == "delete"))
async def delete_button_handler(call: CallbackQuery, callback_data: MenuAction, i18n: I18nContext):
    parent_id = callback_data.parent_id
    grandparent_id = database.get_parent_of(parent_id)

    database.delete_button_by_id(parent_id)

    new_markup = build_dynamic_menu(str(grandparent_id), call.from_user.id, i18n=i18n)
    
    await call.message.edit_text(i18n.get("folder_deleted_returning_stepback"), reply_markup=new_markup)
    await call.answer(i18n.get("deleting-success"))


@utils_router.message(create_button.get_name)
async def createButtonhandle(msg: Message, state: FSMContext, i18n: I18nContext):
    name = msg.text
    data = await state.get_data()
    parent_id = data.get("par_id")
    await state.clear()

    database.create_inline_button(name, parent_id)
    new_keyboard = build_dynamic_menu(parent_id, msg.from_user.id, i18n=i18n)

    await msg.answer(text=f"{i18n.get('succssfully_added_new_button-button')}: {name}", reply_markup=new_keyboard)


@utils_router.callback_query(MenuAction.filter(F.action == "open"))
async def navigate_menu(call: CallbackQuery, callback_data: MenuAction, i18n: I18nContext):
    try:
        markup = build_dynamic_menu(parent_id=callback_data.parent_id, user_id=call.from_user.id, i18n=i18n)
        folder_text = i18n.get("exact_folder", folder_name=callback_data.parent_id)
        await call.message.edit_text(text=folder_text, reply_markup=markup)
        await call.answer()
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        await call.answer("Error building menu.")


@utils_router.message(F.text == "help")
async def menu1_hundel(msg: Message):
    await msg.reply(text="use this instruction")


@utils_router.callback_query()
async def unknown_callback(call: CallbackQuery, i18n: I18nContext):
    await call.answer(i18n.get("button-nothing_message"))


def build_dynamic_menu(parent_id: str, user_id: int | str, i18n: I18nContext):
    builder = InlineKeyboardBuilder()
    children = database.get_buttons_by_parent(parent_id)
    
    # إضافة أزرار المجلدات الفرعية
    for child_id, name in children:
        builder.button(
            text=f"📁 {name}", 
            callback_data=MenuAction(action="open", parent_id=str(child_id)).pack()
        )
    
    controls = []
    is_root = parent_id is None or str(parent_id).upper() in ["NONE", "NULL"]
    admin_list = database.get_admin_ids()
    
    # أزرار لجميع المستخدمين
    if not is_root:
        grandparent = database.get_parent_of(parent_id)
        controls.append(InlineKeyboardButton(text=i18n.get("btn-back"), callback_data=MenuAction(action="open", parent_id=str(grandparent)).pack()))
        controls.append(InlineKeyboardButton(text=i18n.get("btn-send-files"), callback_data=MenuAction(action="send_file", parent_id=parent_id).pack()))
        controls.append(InlineKeyboardButton(text=i18n.get("btn-send-file-list"), callback_data=MenuAction(action="send_flist", parent_id=parent_id).pack()))
        
        if grandparent is not None:
            controls.append(InlineKeyboardButton(text=i18n.get("btn-back-main"), callback_data=MenuAction(action="back_to_main", parent_id=parent_id).pack()))
            
    if is_root:
        controls.append(InlineKeyboardButton(text=i18n.get("btn-start-menu"), callback_data="startMenu"))

    # أزرار المشرفين
    if str(user_id) in admin_list or user_id == RONWER_ID:
        if is_root and parent_id:
            controls.append(InlineKeyboardButton(text=i18n.get("btn-send-admin-list"), callback_data=MenuAction(action="send_admin_list", parent_id=parent_id).pack()))
            controls.append(InlineKeyboardButton(text=i18n.get("btn-broadcast"), callback_data=MenuAction(action="proadcast", parent_id=parent_id).pack()))

        controls.append(InlineKeyboardButton(text=i18n.get("btn-add"), callback_data=MenuAction(action="add", parent_id=parent_id).pack()))
        
        if not is_root:
            controls.append(InlineKeyboardButton(text=i18n.get("btn-rename"), callback_data=MenuAction(action="RenameF", parent_id=parent_id).pack()))
            controls.append(InlineKeyboardButton(text=i18n.get("btn-del-folder"), callback_data=MenuAction(action="delete", parent_id=parent_id).pack()))
            controls.append(InlineKeyboardButton(text=i18n.get("btn-upload"), callback_data=MenuAction(action="upload", parent_id=parent_id).pack()))
            controls.append(InlineKeyboardButton(text=i18n.get("btn-del-file"), callback_data=MenuAction(action="delete_f", parent_id=parent_id).pack()))
            
    # أزرار المالك       
    if is_root and user_id == RONWER_ID:
        controls.append(InlineKeyboardButton(text=i18n.get("btn-add-admin"), callback_data=MenuAction(action="add_admin", parent_id=parent_id).pack()))
        controls.append(InlineKeyboardButton(text=i18n.get("btn-select-supp-group"), callback_data=MenuAction(action="select_supp_group", parent_id=parent_id).pack()))
        controls.append(InlineKeyboardButton(text=i18n.get("btn-remove-admin"), callback_data=MenuAction(action="remove_admin_list", parent_id=parent_id).pack()))

    builder.row(*controls)
    builder.adjust(2)
    return builder.as_markup()


async def safe_broadcast(bot, admin_chat_id: int, broadcast_message, i18n: I18nContext):
    successful = 0
    blocked = 0
    failed = 0

    for user_id in database.get_users():
        try:
            await broadcast_message.copy_to(chat_id=user_id)
            successful += 1
            await asyncio.sleep(0.05)

        except database.TelegramForbiddenError:
            blocked += 1
            database.mark_user_as_inactive(user_id)

        except database.TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            try:
                await broadcast_message.copy_to(chat_id=user_id)
                successful += 1
            except Exception:
                failed += 1

        except Exception:
            failed += 1

    report = (
            f"<b>{i18n.get('exact-broadcast-finished')}</b>\n\n"
            f"{i18n.get('exact-success', count=successful)}\n"
            f"{i18n.get('exact-blocked', count=blocked)}\n"
            f"{i18n.get('exact-faild', count=failed)}"
        )
    await bot.send_message(chat_id=admin_chat_id, text=report, parse_mode="HTML")