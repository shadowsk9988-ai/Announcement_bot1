# main.py
# ----------------------------------------------------------------------
# Telegram Announcement Bot - aiogram 3.x
#
# Features:
#   1. /start command
#   2. Private control panel
#   3. Auto-save every group where the bot becomes admin
#   4. Show all connected groups
#   5. Select All / 6. Unselect All / 7. Select individual groups
#   8. Send Announcement button
#   9. Send Text message
#   10. Send Photo with Caption
#   11. Copy the same message to all selected groups
#   12. Show success / failed count after sending
#   13. Handle FloodWait automatically
#   14. No duplicate groups (enforced by DB UNIQUE constraint)
# ----------------------------------------------------------------------

import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatMemberStatus, ChatType, ParseMode
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message

import database as db
from config import ADMIN_IDS, BOT_TOKEN
from keyboards import (
    cancel_kb,
    confirm_kb,
    groups_list_kb,
    main_menu_kb,
    message_type_kb,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()


# ----------------------------------------------------------------------
# FSM states
# ----------------------------------------------------------------------
class Announcement(StatesGroup):
    waiting_text = State()
    waiting_photo = State()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def get_selected(state: FSMContext) -> set:
    data = await state.get_data()
    return set(data.get("selected", []))


async def set_selected(state: FSMContext, selected: set) -> None:
    await state.update_data(selected=list(selected))


# ----------------------------------------------------------------------
# /start and control panel
# ----------------------------------------------------------------------
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext) -> None:
    if message.chat.type != ChatType.PRIVATE:
        return  # panel only works in private chat

    if not is_admin(message.from_user.id):
        await message.answer("⛔ You are not authorized to use this bot.")
        return

    await state.clear()
    await message.answer(
        "👋 <b>Welcome to the Announcement Bot Control Panel</b>\n\n"
        "Use the buttons below to manage your groups and send announcements.",
        reply_markup=main_menu_kb(),
    )


@router.callback_query(F.data == "back_main")
async def cb_back_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "👋 <b>Announcement Bot Control Panel</b>\n\n"
        "Use the buttons below to manage your groups and send announcements.",
        reply_markup=main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


# ----------------------------------------------------------------------
# Group tracking - auto save/remove when bot's membership changes
# ----------------------------------------------------------------------
@router.my_chat_member()
async def on_bot_membership_change(event: ChatMemberUpdated) -> None:
    if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    new_status = event.new_chat_member.status
    chat_id = event.chat.id
    title = event.chat.title or "Unnamed group"

    if new_status == ChatMemberStatus.ADMINISTRATOR:
        db.add_group(chat_id, title)
        logger.info("Group saved: %s (%s)", title, chat_id)
    elif new_status in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.KICKED,
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.RESTRICTED,
    ):
        # Bot was removed, or demoted from admin -> stop tracking the group
        if db.group_exists(chat_id):
            db.remove_group(chat_id)
            logger.info("Group removed: %s (%s)", title, chat_id)


# ----------------------------------------------------------------------
# View / select groups
# ----------------------------------------------------------------------
@router.callback_query(F.data == "view_groups")
async def cb_view_groups(callback: CallbackQuery, state: FSMContext) -> None:
    groups = db.get_all_groups()
    selected = await get_selected(state)
    text = (
        f"📋 <b>Connected Groups</b> ({len(groups)})\n\n"
        "Tap a group to select/unselect it for the next announcement."
    )
    await callback.message.edit_text(text, reply_markup=groups_list_kb(groups, selected))
    await callback.answer()


@router.callback_query(F.data.startswith("toggle:"))
async def cb_toggle_group(callback: CallbackQuery, state: FSMContext) -> None:
    chat_id = int(callback.data.split(":", 1)[1])
    selected = await get_selected(state)

    if chat_id in selected:
        selected.discard(chat_id)
    else:
        selected.add(chat_id)
    await set_selected(state, selected)

    groups = db.get_all_groups()
    try:
        await callback.message.edit_reply_markup(
            reply_markup=groups_list_kb(groups, selected)
        )
    except TelegramBadRequest:
        pass  # message not modified, safe to ignore
    await callback.answer()


@router.callback_query(F.data == "select_all")
async def cb_select_all(callback: CallbackQuery, state: FSMContext) -> None:
    groups = db.get_all_groups()
    selected = {chat_id for _id, chat_id, _title in groups}
    await set_selected(state, selected)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=groups_list_kb(groups, selected)
        )
    except TelegramBadRequest:
        pass
    await callback.answer("All groups selected ✅")


@router.callback_query(F.data == "unselect_all")
async def cb_unselect_all(callback: CallbackQuery, state: FSMContext) -> None:
    groups = db.get_all_groups()
    await set_selected(state, set())
    try:
        await callback.message.edit_reply_markup(
            reply_markup=groups_list_kb(groups, set())
        )
    except TelegramBadRequest:
        pass
    await callback.answer("Selection cleared")


# ----------------------------------------------------------------------
# Send announcement flow
# ----------------------------------------------------------------------
@router.callback_query(F.data == "ask_send")
async def cb_ask_send(callback: CallbackQuery, state: FSMContext) -> None:
    selected = await get_selected(state)
    if not selected:
        await callback.answer(
            "⚠️ No groups selected. Go to 'View Groups' and select at least one.",
            show_alert=True,
        )
        return

    await callback.message.edit_text(
        f"📢 <b>Send Announcement</b>\n\n"
        f"Selected groups: <b>{len(selected)}</b>\n\n"
        "Choose the type of message you want to send:",
        reply_markup=message_type_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "type_text")
async def cb_type_text(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Announcement.waiting_text)
    await callback.message.edit_text(
        "📝 Send me the <b>text message</b> you want to broadcast.",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "type_photo")
async def cb_type_photo(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Announcement.waiting_photo)
    await callback.message.edit_text(
        "🖼 Send me the <b>photo</b> (with an optional caption) you want to broadcast.",
        reply_markup=cancel_kb(),
    )
    await callback.answer()


@router.message(Announcement.waiting_text, F.text)
async def receive_text(message: Message, state: FSMContext) -> None:
    await state.update_data(msg_type="text", text=message.text)
    selected = await get_selected(state)
    await message.answer(
        f"👀 <b>Preview</b>\n\n{message.text}\n\n"
        f"This will be sent to <b>{len(selected)}</b> group(s). Confirm?",
        reply_markup=confirm_kb(),
    )


@router.message(Announcement.waiting_photo, F.photo)
async def receive_photo(message: Message, state: FSMContext) -> None:
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    await state.update_data(msg_type="photo", photo_id=photo_id, caption=caption)
    selected = await get_selected(state)
    await message.answer_photo(
        photo=photo_id,
        caption=f"👀 Preview above.\n\nThis will be sent to <b>{len(selected)}</b> group(s). Confirm?",
        reply_markup=confirm_kb(),
    )


@router.message(Announcement.waiting_photo)
async def receive_photo_invalid(message: Message) -> None:
    await message.answer("⚠️ Please send a photo, or press Cancel below.", reply_markup=cancel_kb())


@router.message(Announcement.waiting_text)
async def receive_text_invalid(message: Message) -> None:
    await message.answer("⚠️ Please send a text message, or press Cancel below.", reply_markup=cancel_kb())


# ----------------------------------------------------------------------
# Broadcast with FloodWait handling
# ----------------------------------------------------------------------
async def send_to_group(bot: Bot, chat_id: int, data: dict) -> bool:
    """Send the announcement to a single group. Returns True on success.
    Automatically waits out FloodWait (TelegramRetryAfter) and retries."""
    for attempt in range(3):
        try:
            if data.get("msg_type") == "photo":
                await bot.send_photo(
                    chat_id=chat_id,
                    photo=data["photo_id"],
                    caption=data.get("caption") or None,
                )
            else:
                await bot.send_message(chat_id=chat_id, text=data["text"])
            return True
        except TelegramRetryAfter as e:
            logger.warning("FloodWait on %s: sleeping %s sec", chat_id, e.retry_after)
            await asyncio.sleep(e.retry_after + 1)
            continue  # retry after waiting
        except (TelegramForbiddenError, TelegramBadRequest) as e:
            logger.warning("Failed to send to %s: %s", chat_id, e)
            return False
        except Exception as e:  # noqa: BLE001 - catch-all so one bad chat doesn't crash the run
            logger.warning("Unexpected error sending to %s: %s", chat_id, e)
            return False
    return False


@router.callback_query(F.data == "confirm_send")
async def cb_confirm_send(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    selected = set(data.get("selected", []))

    if not selected or "msg_type" not in data:
        await callback.answer("Nothing to send.", show_alert=True)
        return

    await callback.message.edit_text("⏳ Sending announcement, please wait...")
    await callback.answer()

    bot = callback.bot
    success, failed = 0, 0

    for chat_id in selected:
        ok = await send_to_group(bot, chat_id, data)
        if ok:
            success += 1
        else:
            failed += 1
        await asyncio.sleep(0.1)  # small delay to be gentle on Telegram's rate limits

    await state.update_data(msg_type=None, text=None, photo_id=None, caption=None)
    await state.set_state(None)

    await callback.message.answer(
        "✅ <b>Announcement Sent</b>\n\n"
        f"📨 Success: <b>{success}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"📊 Total groups: <b>{len(selected)}</b>",
        reply_markup=main_menu_kb(),
    )


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
async def main() -> None:
    db.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started. Polling for updates...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
