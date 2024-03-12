from kani import Kani, ai_function, ChatMessage
from kani.engines.openai import OpenAIEngine

# local imports
from ..utils.consts import get_openai_api_key


class DescriptorKani(Kani):

    system_instructions = """You are the narrator for a text adventure game. 
        You create short, evocative descriptions of the scenes in the game.
        Include descriptions of the items and exits available to the current player."""
    
    def __init__(self,
                 character,
                 **kwargs):
        super().__init__(**kwargs)
        self.character = character

    def convert_memory_to_chatmessage(self, memory):
        if memory["role"] == "assistant":
            message = ChatMessage.assistant(memory["content"])
        elif memory["role"] == "user":
            message = ChatMessage.user(memory["content"])
        return message

    async def add_to_history(self, memory, *args, **kwargs):
        message = self.convert_memory_to_chatmessage(memory)
        await super().add_to_history(message, *args, **kwargs)
