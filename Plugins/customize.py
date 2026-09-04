from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from info import DATABASE_URI

mongo_client = MongoClient(DATABASE_URI)
mongo_db = mongo_client["cloned_bots"]
bots_col = mongo_db["bots"]


def get_user_bots(user_id):
    return list(bots_col.find(
        {"user_id": int(user_id)},
        {"bot_id": 1, "username": 1, "name": 1}
    ))


def customize_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "Cʟᴏɴᴇ Sᴇᴛᴛɪɴɢs",
            callback_data="mc_clone_settings"
        )],
        [InlineKeyboardButton(
            "Mᴏᴠɪᴇ Fɪʟᴛᴇʀ",
            callback_data="mc_movie_filter"
        )],
        [InlineKeyboardButton(
            "❌ Cʟᴏsᴇ",
            callback_data="mc_close"
        )]
    ])


@Client.on_message(filters.command("customize") & filters.private)
async def customize(client, message):
    await message.reply_text(
        "<b>⚙️ Cᴜsᴛᴏᴍɪᴢᴇ</b>\n\n"
        "Cʜᴏᴏsᴇ ᴡʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ cᴜsᴛᴏᴍɪᴢᴇ:",
        reply_markup=customize_keyboard()
    )


@Client.on_callback_query(filters.regex("^mc_clone_settings$"))
async def clone_settings(client, query):
    bots = get_user_bots(query.from_user.id)
    if not bots:
        await query.answer(
            "Nᴏ ᴄʟᴏɴᴇᴅ ʙᴏᴛs ғᴏᴜɴᴅ. Cʟᴏɴᴇ ᴀ ʙᴏᴛ ғɪʀsᴛ.",
            show_alert=True
        )
        return

    rows = []
    for bot in bots[:30]:
        username = bot.get("username")
        name = bot.get("name") or "Bᴏᴛ"
        bot_id = bot.get("bot_id")
        label = f"@{username}" if username else name[:28]
        rows.append([
            InlineKeyboardButton(
                f"⚙️ {label}",
                callback_data=f"mc_pick:{bot_id}"
            )
        ])
    rows.append([
        InlineKeyboardButton("↩️ Bᴀᴄᴋ", callback_data="mc_back")
    ])

    await query.message.edit_text(
        "<b>⚙️ Cʟᴏɴᴇ Sᴇᴛᴛɪɴɢs</b>\n\n"
        "Sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴄʟᴏɴᴇᴅ ᴀᴜᴛᴏ ғɪʟᴛᴇʀ ʙᴏᴛ:",
        reply_markup=InlineKeyboardMarkup(rows)
    )
    await query.answer()


@Client.on_callback_query(filters.regex(r"^mc_pick:"))
async def pick_clone(client, query):
    try:
        bot_id = int(query.data.split(":", 1)[1])
    except Exception:
        await query.answer("Iɴᴠᴀʟɪᴅ ʙᴏᴛ.", show_alert=True)
        return

    bot = bots_col.find_one({
        "bot_id": bot_id,
        "user_id": int(query.from_user.id)
    })
    if not bot:
        await query.answer("Tʜɪs ɪs ɴᴏᴛ ʏᴏᴜʀ ʙᴏᴛ.", show_alert=True)
        return

    username = bot.get("username")
    bot_link = f"https://t.me/{username}" if username else None

    buttons = []
    if bot_link:
        buttons.append([
            InlineKeyboardButton("↗️ Oᴘᴇɴ Cʟᴏɴᴇ", url=bot_link)
        ])
    buttons.append([
        InlineKeyboardButton("↩️ Bᴀᴄᴋ", callback_data="mc_clone_settings")
    ])

    await query.message.edit_text(
        "<b>⚙️ Cʟᴏɴᴇ Sᴇᴛᴛɪɴɢs</b>\n\n"
        f"Bᴏᴛ: <code>@{username or 'N/A'}</code>\n\n"
        "Oᴘᴇɴ ᴛʜᴇ ᴄʟᴏɴᴇ ᴀɴᴅ sᴇɴᴅ <code>/customize</code>.\n\n"
        "Tʜᴇ ᴄʟᴏɴᴇ ᴄᴜsᴛᴏᴍɪᴢᴀᴛɪᴏɴ ᴍᴇɴᴜ ɪɴᴄʟᴜᴅᴇs:\n"
        "• Sᴛᴀʀᴛ Tᴇxᴛ\n"
        "• Sᴛᴀʀᴛ Iᴍᴀɢᴇ\n"
        "• Bᴜᴛᴛᴏɴs\n"
        "• Fᴏʀᴄᴇ Sᴜʙsᴄʀɪʙᴇ\n"
        "• Aᴜᴛᴏ Dᴇʟᴇᴛᴇ",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^mc_movie_filter$"))
async def movie_filter(client, query):
    await query.message.edit_text(
        "<b>🎬 Mᴏᴠɪᴇ Fɪʟᴛᴇʀ</b>\n\n"
        "U sᴇ <code>/settings</code> ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜᴇ ᴀᴜᴛᴏ ғɪʟᴛᴇʀ "
        "sᴇᴛᴛɪɴɢs.\n\n"
        "Fʀᴏᴍ Pᴍ, ᴜsᴇ <code>/connect CHAT_ID</code> ғɪʀsᴛ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Bᴀᴄᴋ", callback_data="mc_back")]
        ])
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^mc_back$"))
async def customize_back(client, query):
    await query.message.edit_text(
        "<b>⚙️ Cᴜsᴛᴏᴍɪᴢᴇ</b>\n\n"
        "Cʜᴏᴏsᴇ ᴡʜᴀᴛ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ cᴜsᴛᴏᴍɪᴢᴇ:",
        reply_markup=customize_keyboard()
    )
    await query.answer()


@Client.on_callback_query(filters.regex("^mc_close$"))
async def customize_close(client, query):
    await query.message.delete()
    await query.answer()
