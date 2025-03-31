import logging
import os

import google.generativeai as generai
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters

from bot_utils import CHAT, chat, error_handler, exit, get_info, start

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    load_dotenv()

    generai.configure(api_key=os.getenv("API_KEY_GEMINI"))
    app = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    conversation_handler = ConversationHandler(
        entry_points=[MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, chat)],
        states={
            CHAT: [
                MessageHandler((filters.TEXT | filters.PHOTO) & ~filters.COMMAND, chat),
                CommandHandler("get_info", get_info),
            ],
        },
        fallbacks=[CommandHandler("end", exit)],
    )
    app.add_handler(conversation_handler)

    app.add_error_handler(error_handler)
    # Handle the case when a user sends /start but they're not in a conversation
    app.add_handler(CommandHandler("start", start))

    app.run_polling()


if __name__ == "__main__":
    main()
