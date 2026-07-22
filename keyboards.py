# keyboards.py
# ----------------------------------------------------------------------
# All inline keyboards used by the bot are built here.
# ----------------------------------------------------------------------

from typing import List, Set, Tuple

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 View Groups", callback_data="view_groups")
    builder.button(text="📢 Send Announcement", callback_data="ask_send")
    builder.adjust(1)
    return builder.as_markup()


def groups_list_kb(
    groups: List[Tuple[int, int, str]], selected: Set[int]
) -> InlineKeyboardMarkup:
    """Build the group list with a checkbox-style toggle for each group."""
    builder = InlineKeyboardBuilder()

    if not groups:
        builder.row(
            InlineKeyboardButton(text="No groups connected yet", callback_data="noop")
        )
    else:
        for _id, chat_id, title in groups:
            mark = "✅" if chat_id in selected else "⬜"
            label = title if len(title) <= 35 else title[:32] + "..."
            builder.row(
                InlineKeyboardButton(
                    text=f"{mark} {label}", callback_data=f"toggle:{chat_id}"
                )
            )

    builder.row(
        InlineKeyboardButton(text="☑️ Select All", callback_data="select_all"),
        InlineKeyboardButton(text="⬛ Unselect All", callback_data="unselect_all"),
    )
    builder.row(
        InlineKeyboardButton(text="📢 Send Announcement", callback_data="ask_send")
    )
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back_main"))
    return builder.as_markup()


def message_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Text Message", callback_data="type_text")
    builder.button(text="🖼 Photo + Caption", callback_data="type_photo")
    builder.button(text="🔙 Cancel", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Confirm & Send", callback_data="confirm_send")
    builder.button(text="❌ Cancel", callback_data="back_main")
    builder.adjust(1)
    return builder.as_markup()


def cancel_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancel", callback_data="back_main")
    return builder.as_markup()
