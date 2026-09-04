import logging
from pymongo import MongoClient

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from info import DATABASE_URI

logger = logging.getLogger(__name__)

# ============================================================
# DATABASE
# ============================================================

mongo_client = MongoClient(DATABASE_URI)
mongo_db = mongo_client["cloned_bots"]
bots_col = mongo_db.bots


# ============================================================
# PENDING ACTIONS
# ============================================================

# {(bot_id, user_id): "action"}
pending_custom = {}


# ============================================================
# SETTINGS
# ============================================================

def get_settings(bot_id):

    default = {
        "start_text": None,
        "start_image": None,
        "buttons": [],
        "force_sub": None,
        "auto_delete": False
    }

    bot = bots_col.find_one({"bot_id": bot_id})

    if not bot:
        return default

    settings = bot.get("custom_settings", {})

    if settings:
        default.update(settings)

    return default


def save_setting(bot_id, key, value):

    bots_col.update_one(
        {"bot_id": bot_id},
        {
            "$set": {
                f"custom_settings.{key}": value
            }
        },
        upsert=False
    )


# ============================================================
# OWNER CHECK
# ============================================================

def is_owner(bot_id, user_id):

    bot = bots_col.find_one({
        "bot_id": bot_id,
        "user_id": user_id
    })

    return bool(bot)


# ============================================================
# MAIN MENU
# ============================================================

def main_menu():

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📝 Start Text",
                callback_data="cc_start_text"
            ),
            InlineKeyboardButton(
                "🖼️ Start Image",
                callback_data="cc_start_image"
            )
        ],
        [
            InlineKeyboardButton(
                "🔘 Buttons",
                callback_data="cc_buttons"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Force Subscribe",
                callback_data="cc_fsub"
            )
        ],
        [
            InlineKeyboardButton(
                "🗑️ Auto Delete",
                callback_data="cc_autodel"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Close",
                callback_data="cc_close"
            )
        ]
    ])


# ============================================================
# CUSTOMIZATION MENU
# ============================================================

async def show_customize_menu(client, message):

    await message.reply_text(
        "<b>⚙️ Cʟᴏɴᴇ Cᴜsᴛᴏᴍɪᴢᴀᴛɪᴏɴ</b>\n\n"
        "Cʜᴏᴏsᴇ ᴡʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ cᴜsᴛᴏᴍɪᴢᴇ:",
        reply_markup=main_menu()
    )


# ============================================================
# /customize COMMAND
# ============================================================

@Client.on_message(
    filters.command("customize") &
    filters.private
)
async def customize_command(client, message):

    if not is_owner(
        client.me.id,
        message.from_user.id
    ):
        return await message.reply_text(
            "❌ <b>You are not the owner of this clone.</b>"
        )

    await show_customize_menu(
        client,
        message
    )


# ============================================================
# CALLBACK CUSTOMIZE
# ============================================================

@Client.on_callback_query(
    filters.regex("^clone_customize$")
)
async def customize_menu(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ You are not the owner of this clone.",
            show_alert=True
        )

    await query.message.edit_text(
        "<b>⚙️ Cʟᴏɴᴇ Cᴜsᴛᴏᴍɪᴢᴀᴛɪᴏɴ</b>\n\n"
        "Cʜᴏᴏsᴇ ᴡʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ cᴜsᴛᴏᴍɪᴢᴇ:",
        reply_markup=main_menu()
    )

    await query.answer()


# ============================================================
# START TEXT MENU
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_start_text$")
)
async def start_text_button(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    pending_custom[
        (client.me.id, query.from_user.id)
    ] = "start_text"

    settings = get_settings(client.me.id)

    current = settings.get("start_text")

    current_text = ""

    if current:
        current_text = (
            "\n\n<b>Current Start Text:</b>\n"
            f"{current}"
        )

    await query.message.edit_text(
        "<b>📝 Start Text</b>\n\n"
        "Send your new Start Text as a normal message.\n\n"
        "HTML formatting is supported.\n\n"
        "<b>Example:</b>\n"
        "<code>Hello {mention} ❤️</code>"
        f"{current_text}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Cᴀɴᴄᴇʟ",
                    callback_data="cc_cancel"
                )
            ]
        ])
    )

    await query.answer()


# ============================================================
# START IMAGE MENU
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_start_image$")
)
async def start_image_button(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    pending_custom[
        (client.me.id, query.from_user.id)
    ] = "start_image"

    await query.message.edit_text(
        "<b>🖼️ Start Image</b>\n\n"
        "Send the image/photo you want to use "
        "as the Start Image.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Cᴀɴᴄᴇʟ",
                    callback_data="cc_cancel"
                )
            ]
        ])
    )

    await query.answer()


# ============================================================
# BUTTON MENU
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_buttons$")
)
async def buttons_menu(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    pending_custom[
        (client.me.id, query.from_user.id)
    ] = "buttons"

    await query.message.edit_text(
        "<b>🔘 Start Buttons</b>\n\n"
        "Send buttons in this format:\n\n"
        "<code>Button Name - https://example.com</code>\n\n"
        "You can send multiple buttons.\n"
        "Send one button per line.\n\n"
        "<b>Example:</b>\n"
        "<code>"
        "📢 Channel - https://t.me/example\n"
        "💬 Support - https://t.me/example2"
        "</code>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🗑️ Remove All Buttons",
                    callback_data="cc_clear_buttons"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cᴀɴᴄᴇʟ",
                    callback_data="cc_cancel"
                )
            ]
        ])
    )

    await query.answer()


# ============================================================
# CLEAR BUTTONS
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_clear_buttons$")
)
async def clear_buttons(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(
        client.me.id,
        "buttons",
        []
    )

    pending_custom.pop(
        (client.me.id, query.from_user.id),
        None
    )

    await query.answer(
        "✅ All buttons removed.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>🔘 Buttons</b>\n\n"
        "All custom buttons have been removed.",
        reply_markup=main_menu()
    )


# ============================================================
# FORCE SUBSCRIBE MENU
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_fsub$")
)
async def force_sub_button(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    settings = get_settings(client.me.id)

    current = settings.get("force_sub")

    status = "❌ OFF"

    if current:
        status = f"✅ {current}"

    pending_custom[
        (client.me.id, query.from_user.id)
    ] = "force_sub"

    await query.message.edit_text(
        "<b>📢 Force Subscribe</b>\n\n"
        f"<b>Current:</b> {status}\n\n"
        "Send the channel username as a normal message.\n\n"
        "<b>Example:</b>\n"
        "<code>@mychannel</code>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔴 Disable",
                    callback_data="cc_fsub_off"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cᴀɴᴄᴇʟ",
                    callback_data="cc_cancel"
                )
            ]
        ])
    )

    await query.answer()


# ============================================================
# FORCE SUBSCRIBE OFF
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_fsub_off$")
)
async def force_sub_off(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(
        client.me.id,
        "force_sub",
        None
    )

    pending_custom.pop(
        (client.me.id, query.from_user.id),
        None
    )

    await query.answer(
        "✅ Force Subscribe disabled.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>📢 Force Subscribe</b>\n\n"
        "Status: ❌ OFF",
        reply_markup=main_menu()
    )


# ============================================================
# AUTO DELETE MENU
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_autodel$")
)
async def auto_delete_button(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    settings = get_settings(client.me.id)

    enabled = settings.get(
        "auto_delete",
        False
    )

    status = "✅ ON" if enabled else "❌ OFF"

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        f"<b>Current Status:</b> {status}\n\n"
        "Choose an option:",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ ON",
                    callback_data="cc_autodel_on"
                ),
                InlineKeyboardButton(
                    "❌ OFF",
                    callback_data="cc_autodel_off"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="cc_menu"
                )
            ]
        ])
    )

    await query.answer()


# ============================================================
# AUTO DELETE ON
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_autodel_on$")
)
async def auto_delete_on(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(
        client.me.id,
        "auto_delete",
        True
    )

    await query.answer(
        "✅ Auto Delete enabled.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        "Status: ✅ ON",
        reply_markup=main_menu()
    )


# ============================================================
# AUTO DELETE OFF
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_autodel_off$")
)
async def auto_delete_off(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    save_setting(
        client.me.id,
        "auto_delete",
        False
    )

    await query.answer(
        "❌ Auto Delete disabled.",
        show_alert=True
    )

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        "Status: ❌ OFF",
        reply_markup=main_menu()
    )


# ============================================================
# RECEIVE CUSTOM MESSAGES
# ============================================================

@Client.on_message(
    filters.private &
    ~filters.command([
        "start",
        "customize"
    ])
)
async def receive_custom_message(client, message):

    key = (
        client.me.id,
        message.from_user.id
    )

    action = pending_custom.get(key)

    if not action:
        return

    # Owner check
    if not is_owner(
        client.me.id,
        message.from_user.id
    ):
        pending_custom.pop(key, None)
        return

    # --------------------------------------------------------
    # START TEXT
    # --------------------------------------------------------

    if action == "start_text":

        if not message.text:
            return await message.reply_text(
                "❌ Please send text only."
            )

        text = message.text.strip()

        if not text:
            return await message.reply_text(
                "❌ Start Text cannot be empty."
            )

        save_setting(
            client.me.id,
            "start_text",
            text
        )

        pending_custom.pop(key, None)

        await message.reply_text(
            "✅ <b>Start Text Updated Successfully!</b>\n\n"
            f"{text}",
            parse_mode=enums.ParseMode.HTML
        )

        return

    # --------------------------------------------------------
    # START IMAGE
    # --------------------------------------------------------

    if action == "start_image":

        if not message.photo:
            return await message.reply_text(
                "❌ Please send a photo/image."
            )

        file_id = message.photo.file_id

        save_setting(
            client.me.id,
            "start_image",
            file_id
        )

        pending_custom.pop(key, None)

        await message.reply_text(
            "✅ <b>Start Image Updated Successfully!</b>"
        )

        return

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    if action == "buttons":

        if not message.text:
            return await message.reply_text(
                "❌ Please send button details as text."
            )

        lines = message.text.splitlines()

        buttons = []

        for line in lines:

            line = line.strip()

            if not line:
                continue

            if " - " not in line:
                return await message.reply_text(
                    "❌ Invalid button format.\n\n"
                    "Use:\n"
                    "<code>Button Name - https://example.com</code>"
                )

            name, url = line.split(
                " - ",
                1
            )

            name = name.strip()
            url = url.strip()

            if not name or not url:
                return await message.reply_text(
                    "❌ Invalid button format."
                )

            if not (
                url.startswith("https://")
                or url.startswith("http://")
                or url.startswith("tg://")
            ):
                return await message.reply_text(
                    "❌ Invalid URL.\n\n"
                    "URL must start with "
                    "<code>https://</code>"
                )

            buttons.append({
                "name": name,
                "url": url
            })

        if not buttons:
            return await message.reply_text(
                "❌ No valid buttons found."
            )

        save_setting(
            client.me.id,
            "buttons",
            buttons
        )

        pending_custom.pop(key, None)

        keyboard = []

        for button in buttons:

            keyboard.append([
                InlineKeyboardButton(
                    button["name"],
                    url=button["url"]
                )
            ])

        await message.reply_text(
            "✅ <b>Buttons Updated Successfully!</b>\n\n"
            "Your buttons have been saved.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # --------------------------------------------------------
    # FORCE SUBSCRIBE
    # --------------------------------------------------------

    if action == "force_sub":

        if not message.text:
            return await message.reply_text(
                "❌ Please send a channel username."
            )

        channel = message.text.strip()

        if not channel.startswith("@"):
            channel = "@" + channel

        save_setting(
            client.me.id,
            "force_sub",
            channel
        )

        pending_custom.pop(key, None)

        await message.reply_text(
            "✅ <b>Force Subscribe Updated!</b>\n\n"
            f"Channel: <code>{channel}</code>"
        )

        return


# ============================================================
# CANCEL
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_cancel$")
)
async def cancel_custom(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    pending_custom.pop(
        (client.me.id, query.from_user.id),
        None
    )

    await query.message.edit_text(
        "<b>⚙️ Cʟᴏɴᴇ Cᴜsᴛᴏᴍɪᴢᴀᴛɪᴏɴ</b>\n\n"
        "Cʜᴏᴏsᴇ ᴡʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ cᴜsᴛᴏᴍɪᴢᴇ:",
        reply_markup=main_menu()
    )

    await query.answer(
        "❌ Cᴀɴᴄᴇʟled."
    )


# ============================================================
# BACK MENU
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_menu$")
)
async def back_menu(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    pending_custom.pop(
        (client.me.id, query.from_user.id),
        None
    )

    await query.message.edit_text(
        "<b>⚙️ Cʟᴏɴᴇ Cᴜsᴛᴏᴍɪᴢᴀᴛɪᴏɴ</b>\n\n"
        "Cʜᴏᴏsᴇ ᴡʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ cᴜsᴛᴏᴍɪᴢᴇ:",
        reply_markup=main_menu()
    )

    await query.answer()


# ============================================================
# CLOSE
# ============================================================

@Client.on_callback_query(
    filters.regex("^cc_close$")
)
async def close_menu(client, query):

    if not is_owner(
        client.me.id,
        query.from_user.id
    ):
        return await query.answer(
            "❌ Owner only.",
            show_alert=True
        )

    pending_custom.pop(
        (client.me.id, query.from_user.id),
        None
    )

    await query.message.delete()

    await query.answer()
