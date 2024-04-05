import tiktoken
from text_adventure_games.gpt.gpt_helpers import limit_context_length
from ..utils.general import set_up_openai_client
from ..agent.agent_cognition.retrieve import retrieve

GPT4_MAX_TOKENS = 8192
ACTION_MAX_OUTPUT = 100


class Dialogue:
    """This class handles dialogue happening between 2 or more characters.
    """

    def __init__(self, game, participants):
        """
        Args:
            participants (List(Character)): sorted list of 
            characters by initiative.
        """
        self.client = set_up_openai_client(org='Helicone')
        self.verbose = False
        self.gpt_model = "gpt-4"
        self.max_output_tokens = 256  # You get to pick this
        self.max_tokens = 8192-self.max_output_tokens  # GPT-4's max total tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.game = game
        self.participants = participants
        self.characters_system = {}
        self.participants_number = len(participants)
        self.dialogue_history = f'The dialogue between {} just started.'
        self.max_tokens = 1000
        for participant in self.participants:
            self.characters_system[participant.name] = self.get_system_instructions(
                participant)

    def get_system_instructions(self, character):
        system_instructions = f"WORLD INFO: {self.game.world_info}" + "\n"
        system_instructions += f"You are {character.persona.summary}"+ "\n"
        system_instructions += f"GOALS: {character.goals}. " + "/n"
        system_instructions += "These are select MEMORIES in ORDER from LEAST to MOST RELEVANT: "
        context_list = retrieve(self.game, character, query=None, n=-1) #TODO: add query with context of dialogue
        #TODO: Add retrieve only if new characters are mentioned. 

        # limit the context length here on the retrieved memories
        context_list = limit_context_length(context_list,
                                            max_tokens=GPT4_MAX_TOKENS-ACTION_MAX_OUTPUT,
                                            tokenizer=self.game.parser.tokenizer)
        # Then add these to the user message
        print(
            f"passing {len(context_list)} relevant memories to {character.name}")
        system_instructions += "".join([f"{m}\n" for m in context_list])
        system_instructions += (f"""You are in dialogue with:
                                {', '.join([x.name for x in self.participants if x.name != character.name])}.\n""")
        system_instructions += (f"""When it's your turn to speak,
                                you can say something or walk away form the conversation.
                                If you say something, start with: '{character.name} says: '.
                                If you walk away, say only: '{character.name} leaves the conversation.'.
                                If you feel like the last two lines have not added new information
                                or people are speaking in circles, end the conversation.""")
        return system_instructions

    def get_dialogue_history(self):
        return self.dialogue_history

    def add_to_dialogue_history(self, message):
        self.dialogue_history += '\n' + message

    def get_gpt_response(self, character):
        try:
            messages = [{
                "role": "system",
                "content": self.characters_system[character.name] #TODO: change to get_system method
            },
                {
                "role": "user",
                "content": self.get_dialogue_history()
            }
            ]
            response = self.client.chat.completions.create(
                model=self.gpt_model,
                messages=messages,
                temperature=1,
                max_tokens=self.max_output_tokens,
                top_p=0,
                frequency_penalty=0,
                presence_penalty=0
            )
            content = response.choices[0].message.content
            return content
        except Exception as e:
            return f"Something went wrong with GPT: {e}"

    def is_dialogue_over(self):
        if len(self.participants) <= 1:
            return True
        return False

    def dialogue_loop(self):
        while True:
            for character in self.participants:
                response = self.get_gpt_response(character)
                self.add_to_dialogue_history(response)
                if response == f"{character.name} leaves the conversation.":
                    self.participants.remove(character)
            if self.is_dialogue_over():
                print("The conversation is over")
                break
        return self.dialogue_history
