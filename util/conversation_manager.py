# imports
from util.conversation import Conversation
import logging

logger = logging.getLogger(__name__)


class ConversationManager():
    """
    Class to handle in-memory management of active conversations, delegation of incoming messages
    to those conversations, routing of responses back to the client, and conversation 
    creation/deletion.
    """
    active_conversations: dict

    def __init__(self) -> None:
        
        self.active_conversations = {}

    def handle_message(self, message: str, client_id: str) -> dict:
        """
        Master method to handle any incoming message from a client. This method routes the
        message through the classification and transformation workflows, returning the operation
        and configuration details so it can be executed by another model.

        :param message: The incoming client message that needs to be handled.
        :param client_id: The id of the client.
        """

        # First, check if there is an active conversation for this client.
        if client_id in self.active_conversations.keys():
            logger.debug(f"{client_id} already in active conversation")
            # If there is, delegate the message to that conversation.
            try:
                response = self.active_conversations[client_id].handle_message(message)
            except Exception as e:
                raise e
        else:
            logger.debug(f"{client_id} to create new Conversation")
            # If there is not, create a new conversation and delegate the message to that conversation.
            try:
                self.create_conversation(client_id=client_id)
                response = self.active_conversations[client_id].handle_message(message)
            except Exception as e:
                raise e
        
        # Last, return the operation and configs
        # returns in the format {'operation': message_classification, 'config': message_transformation}
        logger.debug(f"Message handled: {response}")
        return response
    
    def create_conversation(self, client_id: str) -> None:
        """
        Create a new conversation object.

        :param client_id: The id of the client.
        """
        self.active_conversations[client_id] = Conversation(client_id=client_id)

    def update_conversation_logs(self, client_id: str, message: str, role: str) -> None:
        """
        Update the conversation logs for a given conversation.

        :param client_id: The id of the client.
        :param message: The message to add to the conversation log.
        :param role: The role of the message (user or bot).
        """

        # First, check if the client has an active conversation.
        if client_id not in self.active_conversations.keys():
            raise Exception("Client does not have an active conversation...")
        else:
            self.active_conversations[client_id].update_conversation_logs(message=message, role=role)

    def remove_conversation(self, client_id: str) -> None:
        """
        Remove a conversation object.

        :param client_id: The id of the client.
        """
        self.active_conversations.pop(client_id)