import config
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder 
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData
from aiogram_i18n import I18nContext


class support_callback(CallbackData, prefix="supp"):
    chat_id: int
    action: str


support_router = Router()


class chat_support(StatesGroup):
    get_user_message = State()
    get_support_message = State()


@support_router.callback_query(F.data == "sendt_user")
@support_router.callback_query(F.data == "support_state")
async def handle_send_message(call: CallbackQuery, state: FSMContext, i18n: I18nContext):
    await call.answer()
    await call.message.reply(
        text=i18n.get("supp-greeting-prompt", name=call.from_user.full_name)
    )
    await state.set_state(chat_support.get_user_message)


@support_router.message(chat_support.get_user_message)
async def handling_send_message_state(msg: Message, state: FSMContext, i18n: I18nContext):
    user_message = msg.text
    
    settings_data = config.load_settings()
    support_chat_id = settings_data.get("supprot_group")

    if not support_chat_id or support_chat_id == "NULL" or support_chat_id == "":
        await msg.answer(i18n.get("supp-group-not-set"))
        return

    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.get("supp-btn-answer-user", name=msg.from_user.full_name),
        callback_data=support_callback(action="admin_answer", chat_id=msg.chat.id).pack()
    )

    try:
        await msg.bot.send_message(
            text=i18n.get(
                "supp-ticket-format",
                name=msg.from_user.full_name,
                message=user_message
            ),
            chat_id=int(support_chat_id),
            reply_markup=builder.as_markup()
        )
        await msg.answer(text=i18n.get("supp-sent-to-team"))
        await state.clear()
    except Exception as e:
        await msg.answer(i18n.get("supp-group-not-found"))
        print(f"Error sending support ticket: {e}")


@support_router.callback_query(support_callback.filter(F.action == "admin_answer"))
async def handel_support_reply(call: CallbackQuery, state: FSMContext, callback_data: support_callback, i18n: I18nContext):
    await state.update_data(chat_id=str(callback_data.chat_id))
    await state.set_state(chat_support.get_support_message)
    await call.message.answer(text=i18n.get("supp-prompt-reply-input"))
    await call.answer() 


@support_router.message(chat_support.get_support_message)
async def handling_support_reply_state(msg: Message, state: FSMContext, i18n: I18nContext):
    await msg.answer(text=i18n.get("supp-sending-wait"))
    support_message = msg.text
    
    data = await state.get_data()
    str_chat_id = data.get("chat_id")
    chat_id = int(str_chat_id)
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text=i18n.get("supp-btn-reply-user"),
        callback_data="sendt_user"
    )

    await state.clear()

    await msg.bot.send_message(
        text=support_message,
        chat_id=chat_id,
        reply_markup=builder.as_markup()
    )
    await msg.answer(text=i18n.get("supp-reply-sent-success"))