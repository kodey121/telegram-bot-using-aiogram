import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, LinkPreviewOptions
from aiogram.enums import MessageEntityType
from aiogram.utils.keyboard import InlineKeyboardBuilder 
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.markdown import markdown_decoration
from aiogram_i18n import I18nContext

from database import add_link, get_link_by_id, download_flag, reset_downlaod_flag
from VideoDownloader import list_available_formats, download 

# Create the Downloads folder 
base_dir = os.path.dirname(os.path.abspath(__file__))
downloads_path = os.path.join(base_dir, "Downloads")
os.makedirs(downloads_path, exist_ok=True)


class downloadvideo(CallbackData, prefix="video"):
    action: str
    fmt_id: str
    unique_message_id: str
    file_type_note: str

handlerRouter = Router()

# For direct links and text links (e.g. [press me](https://...))
LINK_TYPES = [MessageEntityType.URL, MessageEntityType.TEXT_LINK]

def check_has_link(msg: Message) -> bool:
    entities = msg.entities or msg.caption_entities or []
    return any(entity.type in LINK_TYPES for entity in entities)


@handlerRouter.message(check_has_link)
async def link_receiver(msg: Message, i18n: I18nContext):
    text = msg.text or msg.caption
    entities = msg.entities or msg.caption_entities
    extracted_urls = []
    
    for entity in entities:
        if entity.type == MessageEntityType.URL:
            url = text[entity.offset : entity.offset + entity.length]
            extracted_urls.append(url)
        elif entity.type == MessageEntityType.TEXT_LINK:
            extracted_urls.append(entity.url)

    if not extracted_urls:
        return

    await msg.answer(text=i18n.get("vid-fetching-info"))
    
    url = extracted_urls[0]
    unique_id = f"{msg.chat.id}_{msg.message_id}"

    # Save link to database
    add_link(url, unique_id)

    # Fetch video formats and metadata
    options_list, video_title, video_duration = list_available_formats(url)

    if options_list == "unsupported":
        await msg.answer(i18n.get("vid-unsupported-link"))
        return
    
    if not options_list:
        await msg.answer(i18n.get("vid-failed-fetch"))
        return
    
    builder = InlineKeyboardBuilder()
    has_audio_saved = False
    res_list = []

    for fmt_id, ext, resolution, filesize, note in options_list:
        # Filter unwanted formats
        if ext.lower() in ["mhtml", "m3u8", "none", "webm"] or (filesize == "Unknown" and note != "video"):
            continue

        # Keep only one audio track option
        if note == "audio":
            if has_audio_saved:
                continue
            has_audio_saved = True

        # Deduplicate video resolutions
        if note == "video":
            if resolution in res_list:
                continue
            res_list.append(resolution)

        button_label = (
            f"{ext.upper()} | {resolution} ({filesize})"
            if filesize != "Unknown"
            else f"{ext.upper()} | {resolution}"
        )

        builder.button(
            text=button_label,
            callback_data=downloadvideo(
                action="download",
                fmt_id=fmt_id,
                unique_message_id=unique_id,
                file_type_note=note
            ).pack()
        )
    
    builder.adjust(2)
    
    # Safely escape dynamic variables for MarkdownV2 formatting
    safe_url = markdown_decoration.quote(url)
    safe_caption = markdown_decoration.quote(video_title)
    safe_duration = markdown_decoration.quote(str(video_duration))
    
    await msg.answer(
        text=i18n.get("vid-info-card", url=safe_url, title=safe_caption, duration=safe_duration),
        reply_markup=builder.as_markup(),
        parse_mode="MarkdownV2",
        link_preview_options=LinkPreviewOptions(is_disabled=False)
    )

    await msg.answer(text=i18n.get("vid-expiration-warning"))


@handlerRouter.callback_query(downloadvideo.filter(F.action == "download"))
async def download_file(call: CallbackQuery, callback_data: downloadvideo, i18n: I18nContext):
    await call.answer()
    flag = download_flag(unique_id=callback_data.unique_message_id)

    if flag:
        await call.message.answer(i18n.get("vid-already-downloading"))
        return 
    
    elif flag is None:
        await call.message.answer(i18n.get("vid-session-expired"))
        reset_downlaod_flag(callback_data.unique_message_id)
        return
    
    url = get_link_by_id(callback_data.unique_message_id) 
    
    if not url:
        await call.message.answer(i18n.get("vid-session-expired"))
        reset_downlaod_flag(callback_data.unique_message_id)
        return
    
    current_loop = asyncio.get_running_loop()
    fmt_id = callback_data.fmt_id
    status_msg = await call.message.answer(i18n.get("vid-downloading-status"))
    file_path = None

    try:
        file_path, file_type = await download(
            url,
            fmt_id,
            callback_data.file_type_note,
            call.bot,
            call.message.chat.id,
            status_msg.message_id,
            current_loop
        )
        
        if file_path == "timeout":
            await call.message.answer(i18n.get("vid-timeout-error"))
            return
            
        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError("Downloaded file path could not be resolved.")

        await status_msg.edit_text(i18n.get("vid-uploading-status"))
        
        if file_type == "video":
            await call.message.answer_video(video=FSInputFile(file_path))
        else:
            await call.message.answer_audio(audio=FSInputFile(file_path))

        await status_msg.delete()
        
    except Exception as e:
        error_msg = str(e)
        await status_msg.edit_text(i18n.get("vid-download-error", error=error_msg))
        
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        else:
            await call.message.answer(i18n.get("vid-link-expired"))

        reset_downlaod_flag(callback_data.unique_message_id)