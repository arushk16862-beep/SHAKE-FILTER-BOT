import logging
from pymongo import MongoClient

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from database.users_chats_db import db
from info import DATABASE_URI

logger = logging.getLogger(__name__)

# ============================================================
# DATABASE
# ============================================================

mongo_client = MongoClient(DATABASE_URI)
mongo_db = mongo_client["cloned_bots"]
bots_col = mongo_db.bots


# ============================================================
# GET CUSTOM SETTINGS
# ============================================================

def get_custom_settings(bot_id):

    default = {
        "start_text": None,
        "start_image": None,
        "buttons": [],
        "force_sub": None,
        "auto_delete": False
    }

    try:
        bot_data = bots_col.find_one(
            {"bot_id": bot_id}
        )

        if not bot_data:
            return default

        settings = bot_data.get(
            "custom_settings",
            {}
        )

        if settings:
            default.update(settings)

        return default

    except Exception as e:
        logger.exception(
            "Failed to get custom settings: %s",
            e
        )
        return default


# ============================================================
# REPLACE VARIABLES
# ============================================================

def format_start_text(text, user, bot_name):

    if not text:
        return text

    try:
        mention = user.mention
    except Exception:
        mention = user.first_name or "User"

    username = (
        f"@{user.username}"
        if user.username
        else ""
    )

    replacements = {
        "{mention}": mention,
        "{name}": user.first_name or "User",
        "{username}": username,
        "{bot_name}": bot_name
    }

    for key, value in replacements.items():
        text = text.replace(
            key,
            str(value)
        )

    return text


# ============================================================
# BUILD CUSTOM BUTTONS
# ============================================================

def build_custom_buttons(
    custom_buttons,
    bot_username
):

    keyboard = []

    if isinstance(custom_buttons, list):

        for button in custom_buttons:

            if not isinstance(button, dict):
                continue

            name = button.get("name")
            url = button.get("url")

            if not name or not url:
                continue

            keyboard.append([
                InlineKeyboardButton(
                    str(name),
                    url=str(url)
                )
            ])

    # --------------------------------------------------------
    # DEFAULT BUTTONS
    # --------------------------------------------------------

    if not keyboard:

        keyboard = [
            [
                InlineKeyboardButton(
                    "🕵️ HELP",
                    callback_data="help"
                )
            ],
            [
                InlineKeyboardButton(
                    "👑 OWNER",
                    callback_data="owner_info"
                ),
                InlineKeyboardButton(
                    "ℹ️ ABOUT",
                    callback_data="about"
                )
            ]
        ]

    # --------------------------------------------------------
    # ADD TO GROUP
    # --------------------------------------------------------

    if bot_username:

        keyboard.append([
            InlineKeyboardButton(
                "➕ ADD ME TO GROUP",
                url=(
                    f"https://t.me/"
                    f"{bot_username}"
                    f"?startgroup=true"
                )
            )
        ])

    return keyboard


# ============================================================
# START COMMAND
# ============================================================

@Client.on_message(
    filters.command("start") &
    filters.private
)
async def clone_start(client, message):

    try:

        user = message.from_user

        if not user:
            return

        # ====================================================
        # SAVE USER
        # ====================================================

        try:

            if not await db.is_user_exist(
                user.id
            ):

                await db.add_user(
                    user.id,
                    user.first_name
                )

        except Exception as e:

            logger.warning(
                "User DB error: %s",
                e
            )

        # ====================================================
        # BOT INFORMATION
        # ====================================================

        bot = await client.get_me()

        bot_id = bot.id

        bot_name = (
            bot.first_name
            or "My Bot"
        )

        bot_username = (
            bot.username
            or ""
        )

        # ====================================================
        # GET CUSTOM SETTINGS
        # ====================================================

        settings = get_custom_settings(
            bot_id
        )

        custom_text = settings.get(
            "start_text"
        )

        custom_image = settings.get(
            "start_image"
        )

        custom_buttons = settings.get(
            "buttons",
            []
        )

        # ====================================================
        # DEFAULT START TEXT
        # ====================================================

        default_text = (
            f"<b>👋 Hello {user.mention}!</b>\n\n"
            f"🤖 Welcome to <b>{bot_name}</b>.\n\n"
            "Send me a movie name to search."
        )

        # ====================================================
        # CUSTOM START TEXT
        # ====================================================

        if custom_text:

            text = format_start_text(
                custom_text,
                user,
                bot_name
            )

        else:

            text = default_text

        # ====================================================
        # BUTTONS
        # ====================================================

        keyboard = build_custom_buttons(
            custom_buttons,
            bot_username
        )

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        # ====================================================
        # SEND START IMAGE
        # ====================================================

        if custom_image:

            try:

                await message.reply_photo(
                    photo=custom_image,
                    caption=text,
                    reply_markup=reply_markup,
                    parse_mode=enums.ParseMode.HTML
                )

                return

            except Exception as e:

                logger.warning(
                    "Custom start image failed: %s",
                    e
                )

        # ====================================================
        # SEND NORMAL START MESSAGE
        # ====================================================

        await message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        logger.exception(
            "Start command error"
        )

        try:

            await message.reply_text(
                "<b>⚠️ Start Error</b>\n\n"
                f"<code>{e}</code>",
                parse_mode=enums.ParseMode.HTML
            )

        except Exception:

            pass
