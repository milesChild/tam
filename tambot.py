from util import telegrambot
from util import handlers
import config as cfg
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

logging.basicConfig(
    filename='/opt/ft/global/tambot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

if __name__ == '__main__':
    application = ApplicationBuilder().token(cfg.telegram_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", telegrambot.start)],
        states={
            0: [MessageHandler(None, telegrambot.god_handler)],
            1: [MessageHandler(filters.Regex(cfg.user_registration_passcode), telegrambot.register),
                MessageHandler(None, telegrambot.start)
                ],
            2: [CallbackQueryHandler(handlers.confirm_trade)]
        },
        fallbacks=[CommandHandler("cancel", handlers.get_last_trade)],
    )

    application.add_handler(conv_handler)
    application.run_polling()
