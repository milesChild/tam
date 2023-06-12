from util.handlers import (
    help,
    create_ticket,
    register_cpty,
    cancel_ticket,
    modify_ticket,
    lock_trade,
    get_trade_history,
    get_last_trade
)
import logging

logger = logging.getLogger(__name__)

OPERATION_MAP = {
    'help': help,
    'create_ticket': create_ticket,
    'register_cpty': register_cpty,
    'cancel_ticket': cancel_ticket,
    'modify_ticket': modify_ticket,
    'confirm_trade': lock_trade,
    'get_trade_history': get_trade_history,
    'get_last_trade': get_last_trade
}


class OperationExecutor():
    """
    Class to manage the execution of operations that output string text which can be
    transmitted as a response by the bot to the client.
    """

    def __init__(self) -> None:
        pass

    def execute(self, operation: str, config: dict) -> str:
        """
        Method that accepts an operations and its user-scraped configs, delegates work to the
        appropriate handler, and returns the string response that is transmitted back to the user.

        :param operation: The operation to execute.
        :param config: The configuration for the operation.
        """
        if operation not in OPERATION_MAP:
            return f"Unsupported operation: {operation}"
        else:
            return OPERATION_MAP[operation](config)
