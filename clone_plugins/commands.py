import logging
from pymongo import MongoClient

from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from info import DATABASE_URI, ADMINS

logger = logging.getLogger(__name__)


# =========================================================
# MONGODB
# =========================================================

mongo_client = MongoClient(DATABASE_URI)

mongo_db = mongo_client["cloned_bots"]
bots_col = mongo_db["bots"]


# =========================================================
# TEMPORARY USER STATES
# =========================================================

WAITING = {}


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(user_id):
    try:
        return int(user_id) in [int(x) for x in ADMINS]
    except Exception:
        return str(user_id) in [str(x) for x in ADMINS]


# =========================================================
# DEFAULT SETTINGS
# =========================================================

DEFAULT_SETTINGS = {
    "start_text": None,
    "start_image": None,
    "buttons": [],
    "force_sub": None,
    "auto_delete": False
}


# =========================================================
# GET SETTINGS
# =========================================================

def get_custom_settings(bot_id):

    try:
        bot = bots_col.find_one({
            "bot_id": int(bot_id)
        })

        settings = DEFAULT_SETTINGS.copy()

        if bot:
            custom = bot.get("custom_settings", {})

            if isinstance(custom, dict):
                settings.update(custom)

        return settings

    except Exception as e:
        logger.exception(
            "Error getting custom settings: %s",
            e
        )

        return DEFAULT_SETTINGS.copy()


# =========================================================
# SAVE SETTING
# =========================================================

def save_setting(bot_id, key, value):

    try:
        bots_col.update_one(
            {
                "bot_id": int(bot_id)
            },
            {
                "$set": {
                    f"custom_settings.{key}": value
                }
            },
            upsert=False
        )

        return True

    except Exception as e:
        logger.exception(
            "Error saving custom setting: %s",
            e
        )

        return False


# =========================================================
# GET CUSTOM START TEXT
# =========================================================

def get_custom_start_text(bot_id):

    settings = get_custom_settings(bot_id)

    return settings.get("start_text")


# =========================================================
# GET CUSTOM START IMAGE
# =========================================================

def get_custom_start_image(bot_id):

    settings = get_custom_settings(bot_id)

    return settings.get("start_image")


# =========================================================
# GET CUSTOM BUTTONS
# =========================================================

def get_custom_buttons(bot_id):

    settings = get_custom_settings(bot_id)

    buttons = settings.get("buttons", [])

    if not isinstance(buttons, list):
        return []

    return buttons


# =========================================================
# MAIN CUSTOMIZE MENU
# =========================================================

def customize_keyboard():

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
                "🔘 Start Buttons",
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


# =========================================================
# /CUSTOMIZE
# =========================================================

@Client.on_message(
    filters.command("customize") &
    filters.private
)
async def customize_command(client, message):

    if not is_admin(message.from_user.id):
        return await message.reply_text(
            "❌ <b>Owner/Admin only.</b>",
            parse_mode=enums.ParseMode.HTML
        )

    await message.reply_text(
        "<b>⚙️ Clone Customization</b>\n\n"
        "Choose what you want to customize:",
        reply_markup=customize_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )


# =========================================================
# CUSTOMIZE CALLBACK
# =========================================================

@Client.on_callback_query(
    filters.regex("^clone_customize$")
)
async def customize_callback(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    await query.message.edit_text(
        "<b>⚙️ Clone Customization</b>\n\n"
        "Choose what you want to customize:",
        reply_markup=customize_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer()


# =========================================================
# START TEXT MENU
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_start_text$")
)
async def start_text_menu(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    WAITING[query.from_user.id] = {
        "type": "start_text",
        "bot_id": client.me.id
    }

    await query.message.edit_text(
        "<b>📝 Start Text</b>\n\n"
        "Send your new Start Text as a normal message.\n\n"
        "<b>HTML formatting is supported.</b>\n\n"
        "<b>Available placeholders:</b>\n"
        "<code>{mention}</code>\n"
        "<code>{bot_username}</code>\n"
        "<code>{bot_name}</code>\n\n"
        "<b>Example:</b>\n"
        "<code>Hello {mention} ❤️</code>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cc_menu"
                )
            ]
        ]),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer()


# =========================================================
# START IMAGE MENU
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_start_image$")
)
async def start_image_menu(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    WAITING[query.from_user.id] = {
        "type": "start_image",
        "bot_id": client.me.id
    }

    await query.message.edit_text(
        "<b>🖼️ Start Image</b>\n\n"
        "Send the image you want to use as your Start Image.\n\n"
        "Send the image directly here.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cc_menu"
                )
            ]
        ]),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer()


# =========================================================
# BUTTON MENU
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_buttons$")
)
async def buttons_menu(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    WAITING[query.from_user.id] = {
        "type": "buttons",
        "bot_id": client.me.id
    }

    await query.message.edit_text(
        "<b>🔘 Start Buttons</b>\n\n"
        "Send one button per line.\n\n"
        "<b>Format:</b>\n"
        "<code>Button Name - https://example.com</code>\n\n"
        "<b>Example:</b>\n"
        "<code>📢 Updates - https://t.me/example</code>\n"
        "<code>💬 Support - https://t.me/example2</code>",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🗑️ Remove All",
                    callback_data="cc_clear_buttons"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Cancel",
                    callback_data="cc_menu"
                )
            ]
        ]),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer()


# =========================================================
# FORCE SUBSCRIBE MENU
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_fsub$")
)
async def force_sub_menu(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    settings = get_custom_settings(client.me.id)

    current = settings.get("force_sub")

    if current:
        status = f"✅ {current}"
    else:
        status = "❌ OFF"

    WAITING[query.from_user.id] = {
        "type": "force_sub",
        "bot_id": client.me.id
    }

    await query.message.edit_text(
        "<b>📢 Force Subscribe</b>\n\n"
        f"<b>Current:</b> {status}\n\n"
        "Send the channel username.\n\n"
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
                    "⬅️ Back",
                    callback_data="cc_menu"
                )
            ]
        ]),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer()


# =========================================================
# FORCE SUBSCRIBE OFF
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_fsub_off$")
)
async def force_sub_off(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    WAITING.pop(query.from_user.id, None)

    save_setting(
        client.me.id,
        "force_sub",
        None
    )

    await query.message.edit_text(
        "<b>📢 Force Subscribe</b>\n\n"
        "Status: ❌ OFF",
        reply_markup=customize_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer(
        "✅ Force Subscribe disabled.",
        show_alert=True
    )


# =========================================================
# AUTO DELETE MENU
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_autodel$")
)
async def auto_delete_menu(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    settings = get_custom_settings(client.me.id)

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
        ]),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer()


# =========================================================
# AUTO DELETE ON
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_autodel_on$")
)
async def auto_delete_on(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    save_setting(
        client.me.id,
        "auto_delete",
        True
    )

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        "Status: ✅ ON",
        reply_markup=customize_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer(
        "✅ Auto Delete enabled.",
        show_alert=True
    )


# =========================================================
# AUTO DELETE OFF
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_autodel_off$")
)
async def auto_delete_off(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    save_setting(
        client.me.id,
        "auto_delete",
        False
    )

    await query.message.edit_text(
        "<b>🗑️ Auto Delete</b>\n\n"
        "Status: ❌ OFF",
        reply_markup=customize_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer(
        "❌ Auto Delete disabled.",
        show_alert=True
    )


# =========================================================
# CLEAR BUTTONS
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_clear_buttons$")
)
async def clear_buttons(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    WAITING.pop(query.from_user.id, None)

    save_setting(
        client.me.id,
        "buttons",
        []
    )

    await query.message.edit_text(
        "<b>🔘 Start Buttons</b>\n\n"
        "✅ All custom buttons have been removed.",
        reply_markup=customize_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer(
        "✅ Buttons removed.",
        show_alert=True
    )


# =========================================================
# RECEIVE CUSTOMIZATION INPUT
# =========================================================

@Client.on_message(
    filters.incoming &
    filters.private
)
async def receive_custom_input(client, message):

    user_id = message.from_user.id

    if not is_admin(user_id):
        return

    if user_id not in WAITING:
        return

    state = WAITING.get(user_id)

    if not state:
        return

    setting_type = state.get("type")
    bot_id = state.get("bot_id")

    # -----------------------------------------------------
    # START TEXT
    # -----------------------------------------------------

    if setting_type == "start_text":

        if not message.text:
            return await message.reply_text(
                "❌ Please send text."
            )

        text = message.text.strip()

        if not text:
            return await message.reply_text(
                "❌ Start Text cannot be empty."
            )

        if save_setting(
            bot_id,
            "start_text",
            text
        ):

            WAITING.pop(user_id, None)

            await message.reply_text(
                "<b>✅ Start Text Updated!</b>\n\n"
                "Now send <code>/start</code> "
                "to check the new Start Text.",
                parse_mode=enums.ParseMode.HTML
            )

        else:

            await message.reply_text(
                "❌ Failed to save Start Text."
            )

        return

    # -----------------------------------------------------
    # START IMAGE
    # -----------------------------------------------------

    if setting_type == "start_image":

        if not message.photo:

            return await message.reply_text(
                "❌ Please send a photo."
            )

        photo_id = message.photo.file_id

        if save_setting(
            bot_id,
            "start_image",
            photo_id
        ):

            WAITING.pop(user_id, None)

            await message.reply_text(
                "<b>✅ Start Image Updated!</b>\n\n"
                "Send <code>/start</code> "
                "to check it.",
                parse_mode=enums.ParseMode.HTML
            )

        else:

            await message.reply_text(
                "❌ Failed to save Start Image."
            )

        return

    # -----------------------------------------------------
    # BUTTONS
    # -----------------------------------------------------

    if setting_type == "buttons":

        if not message.text:
            return await message.reply_text(
                "❌ Please send buttons as text."
            )

        lines = message.text.splitlines()

        buttons = []

        invalid = []

        for line in lines:

            line = line.strip()

            if not line:
                continue

            if " - " not in line:
                invalid.append(line)
                continue

            name, url = line.split(
                " - ",
                1
            )

            name = name.strip()
            url = url.strip()

            if not name or not url:
                invalid.append(line)
                continue

            if not (
                url.startswith("http://")
                or url.startswith("https://")
                or url.startswith("tg://")
            ):
                invalid.append(line)
                continue

            buttons.append({
                "text": name,
                "url": url
            })

        if not buttons:

            return await message.reply_text(
                "<b>❌ No valid buttons found.</b>\n\n"
                "Use:\n"
                "<code>Button Name - https://example.com</code>",
                parse_mode=enums.ParseMode.HTML
            )

        if save_setting(
            bot_id,
            "buttons",
            buttons
        ):

            WAITING.pop(user_id, None)

            preview = ""

            for button in buttons:
                preview += (
                    f"• {button['text']}\n"
                    f"  {button['url']}\n\n"
                )

            await message.reply_text(
                "<b>✅ Buttons Updated!</b>\n\n"
                f"{preview}",
                parse_mode=enums.ParseMode.HTML
            )

        else:

            await message.reply_text(
                "❌ Failed to save buttons."
            )

        return

    # -----------------------------------------------------
    # FORCE SUBSCRIBE
    # -----------------------------------------------------

    if setting_type == "force_sub":

        if not message.text:
            return await message.reply_text(
                "❌ Send a channel username."
            )

        channel = message.text.strip()

        if not channel.startswith("@"):
            channel = "@" + channel

        if save_setting(
            bot_id,
            "force_sub",
            channel
        ):

            WAITING.pop(user_id, None)

            await message.reply_text(
                "<b>✅ Force Subscribe Updated!</b>\n\n"
                f"Channel: <code>{channel}</code>",
                parse_mode=enums.ParseMode.HTML
            )

        else:

            await message.reply_text(
                "❌ Failed to save Force Subscribe."
            )

        return


# =========================================================
# BACK TO MAIN MENU
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_menu$")
)
async def custom_back_menu(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    WAITING.pop(
        query.from_user.id,
        None
    )

    await query.message.edit_text(
        "<b>⚙️ Clone Customization</b>\n\n"
        "Choose what you want to customize:",
        reply_markup=customize_keyboard(),
        parse_mode=enums.ParseMode.HTML
    )

    await query.answer()


# =========================================================
# CLOSE PANEL
# =========================================================

@Client.on_callback_query(
    filters.regex("^cc_close$")
)
async def custom_close(client, query):

    if not is_admin(query.from_user.id):
        return await query.answer(
            "❌ Owner/Admin only.",
            show_alert=True
        )

    WAITING.pop(
        query.from_user.id,
        None
    )

    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(
            "Could not delete customize panel: %s",
            e
        )

    await query.answer()
