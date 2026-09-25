import os
import shutil
import asyncio
from random import randint
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n import I18nContext
import img2pdf
from aiogram.fsm.state import State, StatesGroup

from random import randint
class Photos2pdf(StatesGroup):
    recevingMessage = State()

P2pfrouter = Router()


P2pfrouter = Router()

@P2pfrouter.callback_query(F.data == "Photos2Pdf")
async def p2PfMainHandler(call: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await state.update_data(photo_count=1)
    await state.set_state(Photos2pdf.recevingMessage)
    
    await call.message.answer(text=i18n.get("p2p-send-photos-prompt"))
    await call.answer()


@P2pfrouter.message(Photos2pdf.recevingMessage, F.photo)
async def handling_photos_saving(msg: Message, state: FSMContext, i18n: I18nContext, album: list[Message] = None):
    chat_id = msg.chat.id
    user_id = msg.from_user.id

    per_user_photo_path = os.path.join("Downloads/Photos", f"{chat_id}_{user_id}")
    os.makedirs(per_user_photo_path, exist_ok=True)

    data = await state.get_data()
    photo_count = data.get("photo_count", 1)

    photos_to_process = album if album else [msg]

    try:
        for photo_msg in photos_to_process:
            if not photo_msg.photo:
                continue
                
            photo = photo_msg.photo[-1]
            file_name = f"photo_{photo_count}.jpg"
            destination = os.path.join(per_user_photo_path, file_name)

            await msg.bot.download(file=photo, destination=destination)
            photo_count += 1  

        await state.update_data(photo_count=photo_count)

        # Localized response passing dynamic variable values
        saved_count = len(photos_to_process)
        total_collected = photo_count - 1
        
        await msg.answer(i18n.get("p2p-saved-status", saved=saved_count, total=total_collected))
        
        await state.update_data(chat_id=chat_id)
        await state.update_data(user_id=user_id)
        
        builder = InlineKeyboardBuilder()
        builder.button(text=i18n.get("p2p-btn-done"), callback_data="Done_uploading")

        await msg.answer(text=i18n.get("p2p-finish-instruction"), reply_markup=builder.as_markup())

    except Exception as e:
        print(f"An error occurred while saving photos: {e}")


@P2pfrouter.callback_query(Photos2pdf.recevingMessage, F.data == "Done_uploading")
async def done_fun_handling(call: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await call.answer()
    
    data = await state.get_data()
    chat_id = data.get("chat_id")
    user_id = data.get("user_id")
    
    await call.message.answer(text=i18n.get("p2p-processing"))
    
    per_user_pdf_path = os.path.join("Downloads/Pdfs", f"{chat_id}_{user_id}")
    photos_folder = f"Downloads/Photos/{chat_id}_{user_id}"
    
    try:
        os.makedirs(per_user_pdf_path, exist_ok=True)

        if not os.path.exists(photos_folder):
            await call.message.answer(i18n.get("p2p-no-photos-found"))
            return

        imgs = os.listdir(photos_folder)
        imgs.sort()

        full_img_paths = [os.path.join(photos_folder, img) for img in imgs if img.endswith(".jpg")]

        if not full_img_paths:
            await call.message.answer(i18n.get("p2p-no-photos-found"))
            return
            
        finle_doc_name = f"{user_id}_{randint(0,100)}.pdf"
        output_pdf_file = os.path.join(per_user_pdf_path, finle_doc_name)

        pdf_bytes = await asyncio.to_thread(img2pdf.convert, full_img_paths)

        def save_pdf_file():
            with open(output_pdf_file, "wb") as file:
                file.write(pdf_bytes)
                
        await asyncio.to_thread(save_pdf_file)

        finale_pdf = os.path.join(per_user_pdf_path, finle_doc_name)

        await call.bot.send_document(document=FSInputFile(finale_pdf), chat_id=chat_id)
        
    except Exception as e:
        print(f"An error occurred during PDF generation: {e}")
        await call.message.answer(i18n.get("p2p-generation-error"))
        
    finally:
        if os.path.exists(photos_folder):
            await asyncio.to_thread(shutil.rmtree, photos_folder)
            
        if os.path.exists(per_user_pdf_path):
            await asyncio.to_thread(shutil.rmtree, per_user_pdf_path)
        
        await state.clear()


@P2pfrouter.callback_query(F.data == "Done_uploading")
async def expired_session_sunc(call: CallbackQuery, i18n: I18nContext):
    await call.answer(text=i18n.get("p2p-session-expired"), show_alert=True)