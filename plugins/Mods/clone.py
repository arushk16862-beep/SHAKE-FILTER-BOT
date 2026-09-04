import re
import logging
from pymongo import MongoClient

from pyrogram import Client, filters
from pyrogram.types import Message

from info import API_ID, API_HASH, ADMINS
from info import DATABASE_URI as MONGO_URL

logger = logging.getLogger(__name__)

# MongoDB
mongo_client = MongoClient(MONGO_URL)
mongo_db = mongo_client["cloned_bots"]
bots_collection = mongo_db["bots"]


class clonedme:
    ME = None
    U_NAME = None
    B_NAME = None


# --------------------------------------------------
# CLONE BOT
# --------------------------------------------------

@Client.on_message(
    filters.regex(r"\d{8,10}:[A-Za-z0-9_-]{35}") & filters.private
)
async def on_clone(client, message):
    try:
        # Make sure message contains text
        if not message.text:
            return

        # Extract bot token
        token_match = re.search(
            r"\d{8,10}:[A-Za-z0-9_-]{35}",
            message.text
        )

        if not token_match:
            return

        bot_token = token_match.group(0)

        user_id = message.from_user.id

        # Prevent duplicate clone
        existing = bots_collection.find_one({
            "token": bot_token
        })

        if existing:
            return await message.reply_text(
                "⚠️ This bot is already cloned."
            )

        msg = await message.reply_text(
            "♻️ <b>Trying to clone your bot...</b>\n"
            "Please wait."
        )

        try:
            # Create cloned client
            cloned_bot = Client(
                name=f"clone_{bot_token.split(':')[0]}",
                api_id=API_ID,
                api_hash=API_HASH,
                bot_token=bot_token,
                plugins={"root": "clone_plugins"}
            )

            # Start cloned bot
            await cloned_bot.start()

            bot = await cloned_bot.get_me()

            # Save details
            bot_data = {
                "bot_id": bot.id,
                "is_bot": True,
                "user_id": user_id,
                "name": bot.first_name or "",
                "username": bot.username or "",
                "token": bot_token
            }

            bots_collection.update_one(
                {"bot_id": bot.id},
                {"$set": bot_data},
                upsert=True
            )

            # Update global clone information
            clonedme.ME = bot.id
            clonedme.U_NAME = bot.username
            clonedme.B_NAME = bot.first_name

            await msg.edit_text(
                f"✅ <b>Successfully cloned</b>\n\n"
                f"🤖 Bot: @{bot.username or 'N/A'}\n"
                f"🆔 ID: <code>{bot.id}</code>\n\n"
                f"⚠️ Keep your bot token private."
            )

            logger.info(
                "Bot cloned successfully: @%s",
                bot.username
            )

        except Exception as e:
            logger.exception("Error while cloning bot")

            await msg.edit_text(
                "⚠️ <b>BOT ERROR:</b>\n\n"
                f"<code>{str(e)}</code>"
            )

    except Exception as e:
        logger.exception("Clone handler error: %s", e)


# --------------------------------------------------
# GET CLONED BOT
# --------------------------------------------------

async def get_bot():
    """
    Returns information about the latest cloned bot.
    Does NOT expose the bot token.
    """

    bot_data = bots_collection.find_one(
        {},
        sort=[("_id", -1)]
    )

    if not bot_data:
        return None

    class BotInfo:
        id = bot_data.get("bot_id")
        username = bot_data.get("username")
        first_name = bot_data.get("name")

    return BotInfo()


# --------------------------------------------------
# LIST USER'S CLONED BOTS
# --------------------------------------------------

@Client.on_message(
    filters.command("clonedbots") & filters.private
)
async def cloned_bots_list(client, message):

    try:
        user_id = message.from_user.id

        bots = list(
            bots_collection.find(
                {"user_id": user_id}
            )
        )

        if not bots:
            return await message.reply_text(
                "❌ You haven't cloned any bots yet."
            )

        text = "<b>🤖 Your cloned bots:</b>\n\n"

        for bot in bots:
            username = bot.get("username") or "N/A"
            name = bot.get("name") or "Unknown"
            bot_id = bot.get("bot_id")

            text += (
                f"• @{username}\n"
                f"  Name: {name}\n"
                f"  ID: <code>{bot_id}</code>\n\n"
            )

        await message.reply_text(text)

    except Exception as e:
        logger.exception(
            "Error while listing cloned bots"
        )

        await message.reply_text(
            f"⚠️ Error: <code>{str(e)}</code>"
        )


# --------------------------------------------------
# CLONED BOT COUNT
# --------------------------------------------------

@Client.on_message(
    filters.command("cloned_count") & filters.private
)
async def cloned_count(client, message):

    try:
        user_id = message.from_user.id

        # ADMINS may be int or string
        admin_ids = [str(x) for x in ADMINS]

        if str(user_id) not in admin_ids:
            return await message.reply_text(
                "❌ You are not authorized to use this command."
            )

        count = bots_collection.count_documents({})

        if count == 0:
            return await message.reply_text(
                "❌ No bots have been cloned yet."
            )

        bots = bots_collection.find(
            {},
            {"username": 1, "_id": 0}
        )

        usernames = []

        for bot in bots:
            username = bot.get("username")

            if username:
                usernames.append(f"@{username}")

        text = (
            f"🤖 <b>Total cloned bots:</b> {count}\n\n"
        )

        if usernames:
            text += "\n".join(usernames)

        await message.reply_text(text)

    except Exception as e:
        logger.exception(
            "Error while counting cloned bots"
        )

        await message.reply_text(
            f"⚠️ Error: <code>{str(e)}</code>"
        )


# --------------------------------------------------
# REMOVE CLONED BOT
# --------------------------------------------------

@Client.on_message(
    filters.command("removebot") & filters.private
)
async def remove_bot(client, message):

    try:
        user_id = message.from_user.id
        admin_ids = [str(x) for x in ADMINS]

        if str(user_id) not in admin_ids:
            return await message.reply_text(
                "❌ You are not authorized."
            )

        if len(message.command) < 2:
            return await message.reply_text(
                "Usage:\n"
                "<code>/removebot username</code>\n\n"
                "Example:\n"
                "<code>/removebot mybot</code>"
            )

        username = message.command[1].lstrip("@")

        bot_data = bots_collection.find_one({
            "username": username
        })

        if not bot_data:
            return await message.reply_text(
                f"❌ @{username} is not in the cloned bot list."
            )

        bots_collection.delete_one({
            "_id": bot_data["_id"]
        })

        await message.reply_text(
            f"✅ @{username} removed successfully."
        )

    except Exception as e:
        logger.exception(
            "Error while removing cloned bot"
        )

        await message.reply_text(
            f"⚠️ Error: <code>{str(e)}</code>"
        )


# --------------------------------------------------
# DELETE CLONED BOT BY TOKEN
# --------------------------------------------------

@Client.on_message(
    filters.command("deletecloned") & filters.private
)
async def delete_cloned_bot(client, message):

    try:
        user_id = message.from_user.id
        admin_ids = [str(x) for x in ADMINS]

        if str(user_id) not in admin_ids:
            return await message.reply_text(
                "❌ You are not authorized."
            )

        if len(message.command) < 2:
            return await message.reply_text(
                "Usage:\n"
                "<code>/deletecloned BOT_TOKEN</code>"
            )

        bot_token = message.command[1].strip()

        token_match = re.fullmatch(
            r"\d{8,10}:[A-Za-z0-9_-]{35}",
            bot_token
        )

        if not token_match:
            return await message.reply_text(
                "❌ Invalid bot token format."
            )

        result = bots_collection.delete_one({
            "token": bot_token
        })

        if result.deleted_count:
            await message.reply_text(
                "✅ Cloned bot removed from database."
            )
        else:
            await message.reply_text(
                "❌ This bot is not in the cloned list."
            )

    except Exception as e:
        logger.exception(
            "Error while deleting cloned bot"
        )

        await message.reply_text(
            f"⚠️ Error: <code>{str(e)}</code>"
        )
