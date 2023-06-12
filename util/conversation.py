# imports
from uuid import uuid4
from datetime import datetime
import openai
from prompts.client_prompts import CLASSIFICATION_PROMPT, TRANSFORMATION_PROMPTS_MAP
from prompts.prompts_data import OPERATION_MAP
import config as cfg
import ast
import logging

logger = logging.getLogger(__name__)

# from util.gpt import get_completion_from_messages

openai.api_key = cfg.openai_key

# anything that does not need additional transformations can exit early
EXIT_EARLY_MAP = {'help', 'get_trade_history'}


def get_completion_from_messages(messages, model="gpt-3.5-turbo", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,  # this is the degree of randomness of the model's output
    )

    return response.choices[0].message["content"]


class Conversation():
    """
    Class to represent a conversation between a client and the tam_bot.
    """
    client_id: str
    conversation_id: str
    time_started: str
    conversation_log: list

    def __init__(self, client_id: str) -> None:
        """
        Initialize a conversation object.
        :param client_id: The id of the client.
        """
        self.client_id = client_id
        self.conversation_id = str(uuid4())
        self.time_started = str(datetime.now())
        self.conversation_log = []

    def handle_message(self, message) -> str:
        """
        Master method to handle any incoming message from a client. This method routes the
        message through the classification and transformation workflows, returning the operation
        and configuration details so it can be executed by another model.

        :param message: The incoming client message that needs to be handled.
        """

        # Log the message
        self.add_to_log(role='user', content=message)

        # First, classify the operation
        try:
            message_classification = self.__clasify_operation(message)
        except Exception as e:
            raise e

        logger.debug(f"{self.client_id} {message} {message_classification}")

        # Next, transform the message accordingly.
        try:
            message_transformation = self.__transform_message(
                message=message, operation=message_classification)
        except Exception as e:
            raise e

        # Last, return the operation and configs
        return {'operation': message_classification, 'config': message_transformation}

    def __clasify_operation(self, message: str) -> str:
        """
        Attempt read a client message and interpret which operation it is attempting to perform.
        Uses the classification_prompt and openai api to classify the message.

        :param message: The message to classify.
        :return: The operation of the message.
        """
        try:
            classification_template = [
                {'role': 'system', 'content': CLASSIFICATION_PROMPT},
                {'role': 'user', 'content': message},
            ]
            message_classification = get_completion_from_messages(
                classification_template, temperature=0)
        except Exception as e:
            raise e

        # Second, check to ensure that the message classification is a valid entry in the list of possible operations.
        if message_classification not in [operation['operation'] for operation in OPERATION_MAP]:
            message_classification = 'help'

        return message_classification

    def __transform_message(self, message: str, operation: str) -> dict:
        """
        Attempt to take a client's input message and transform it into a dictionary with the
        appropriate format based on the specified operation.

        :param message: The message to transform.
        :param operation: The operation for which the transformation format will be based on.
        :return: The dict-transformed message.
        """

        logger.debug(f"{self.client_id} {message} {operation}")

        # If the operation is for help, simply add the user_message to the config dict.
        if operation == 'help':
            return {'user_message': message}
        elif operation == 'get_trade_history':
            return {'user_message': operation}

        # Select the appropriate transformation prompt based on the operation.
        try:
            prompt = TRANSFORMATION_PROMPTS_MAP[operation]
        except Exception as e:
            return {}

        # Transform the message.
        try:
            transformation_template = [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': message},
            ]
            message_transformation = get_completion_from_messages(
                transformation_template, temperature=0)
            logging.debug(message_transformation)
        except Exception as e:
            raise e

        # Try to read the message_transformation into a dict.
        try:
            logger.debug(f"Beginning message transform to dictionary {message_transformation}")
            # find the indeces of the first and last curly braces and use
            # ast.literaleval to read the string into a dict.
            d1index = message_transformation.index('{')
            d2index = message_transformation.rindex('}')
            configs = ast.literal_eval(
                message_transformation[d1index:d2index+1])
            return configs
        except Exception as e:
            raise e

    def add_to_log(self, role: str, content: str) -> None:
        """
        Add an interaction to the conversation log.
        :param interaction: The interaction to add in the openai api format 
        of {role: str, content: str}.
        """
        self.conversation_log.append({"role": role, "content": content})
