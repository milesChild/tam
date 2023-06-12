import config as cfg
from util import rds
import telegram
import logging
import os
from util import handlers
from util.conversation import Conversation
from util.conversation_manager import ConversationManager
from util.operation_executor import OperationExecutor
from util.gpt import *
from telegram import Update, BotCommand
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Initialize the Conversation Manager
conversation_manager = ConversationManager()
operation_executor = OperationExecutor()


async def set_tam_commands():
    """ Registers TAM's commands. Add or update to this list as needed."""
    bot = telegram.Bot(cfg.telegram_token)
    async with bot:
        result = await bot.set_my_commands([
            BotCommand('cancel', 'end convo with TAM'),
        ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """For the very beginning of a conversation - starts the ball rolling on
    registration or otherwise throws you right into chatgpt.
    """
    logger.debug(f"Entering start {update} {context}")
    try:
        is_new = _is_new(update.message.from_user.id)
    except Exception as e:
        # to be on the safe side, we will assume that they are not registered on
        # failures to look up user accordingly.
        logger.error(e, exc_info=True)
        is_new = True

    if is_new:
        logger.debug(f"/start debug branch new user")
        txt = "Would you like to register? Please tell me the passcode given to you"
        await context.bot.send_message(text=txt, chat_id=update.message.from_user.id)
        return 1
    else:
        txt = f"""How can I help, {update.message.from_user.first_name}"""
        await context.bot.send_message(text=txt,
                                       chat_id=update.message.from_user.id)
        return 0


async def god_handler(update: Update, context):
    """Handles all incoming messages from the user."""
    logger.debug(f"{update.message.from_user.id} Entering god handler ")

    # If the user is new, wait until they register before proceeding.
    if _is_new(update.message.from_user.id):
        logger.debug(
            f"{update.message.from_user.id} god handling checking onboarding")
        txt = """Hi! Before you can trade with us, you must be onboarded."""
        await context.bot.send_message(text=txt, chat_id=update.message.from_user.id)
        return 1
    else:
        # log message
        handlers._generate_log(
            "CHAT", update.message.from_user.id, update.message.text)

        logger.debug(
            f"{update.message.from_user.id} god handling entering conversation manager")
        message = update.message.text
        id = update.message.from_user.id
        logger.debug(f"{update.message.from_user.id} god to send {message}")

        try:
            response = conversation_manager.handle_message(
                message=message, client_id=id)
            operation = response["operation"]
            config = response["config"]
            config["client_id"] = id
            config["msg"] = message
            config["first_name"] = update.message.from_user.first_name
            our_response = await operation_executor.execute(operation=operation, config=config)
            logger.debug(
                f"{update.message.from_user.id} god to send {our_response}")
        except Exception as e:
            logger.error(e, exc_info=True)
            raise e

        if type(our_response) == tuple:
            # we were given reply_markup
            await context.bot.send_message(text=our_response[0], chat_id=id, reply_markup=our_response[1])
            return 2
        else:
            possible_doc_path = our_response.split("|")
            logger.debug(our_response)
            if os.path.exists(possible_doc_path[0]):
                await context.bot.send_document(chat_id=id, document=open(f'{possible_doc_path[0]}', 'rb'))
                os.remove(possible_doc_path[0])
                our_response = possible_doc_path[1]
            await context.bot.send_message(text=our_response, chat_id=id)
    return 0


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registers a real broker dealer to the user for demo purposes."""
    handlers._generate_log(
        "REGISTER", update.message.from_user.id, update.message.text)
    user_values = _generate_random_user(update.message.from_user.id)

    user_values['first_name'] = update.message.from_user.first_name
    user_values['last_name'] = update.message.from_user.last_name
    user_values['telegram_username'] = update.message.from_user.username

    rds.insert(**cfg.hibiscus_db, table='telegram_users', data=user_values)

    txt = f"""Oh, {update.message.from_user.first_name}? You've been registered, so welcome!"""

    await context.bot.send_message(text=txt, chat_id=update.message.from_user.id)
    return 0


def _is_new(id: int) -> bool:
    """
    Checks to see if user in the chat is a new cp or not and does preliminary
    onboarding if so.

    :param id: id of the telegram user
    :return: True if new, False otherwise
    """
    query = f"""SELECT * from hibiscus.telegram_users WHERE telegram_id={id}"""

    val = rds.run(**cfg.hibiscus_db, query=query, return_dict=True)

    if len(val) > 0:
        return False
    else:
        return True


def _generate_random_user(user_id: int):
    """Given a user id, generate some kind of random registration """
    query = """
    SELECT id from counterparty
    ORDER BY rand()
    LIMIT 1"""

    cp_id = rds.run(**cfg.hibiscus_db, query=query, return_dict=True)[0]['id']
    return {'telegram_id': user_id, 'counterparty_id': cp_id}


async def _do_nothing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # print("Doing nothing")

    return 0
