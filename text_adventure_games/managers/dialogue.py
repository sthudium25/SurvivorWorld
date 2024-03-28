import tiktoken
from ..utils.general import set_up_openai_client


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
        self.max_output_tokens = 256 # You get to pick this
        self.max_tokens = 8192-self.max_output_tokens # GPT-4's max total tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.game = game
        self.participants = participants
        self.characters_system = {}
        self.participants_number = len(participants)
        self.dialogue_history = 'The dialogue just started.'
        self.max_tokens = 1000
        for participant in self.participants:
            self.characters_system[participant.name] = self.get_system_instructions(participant)

    def get_persona(self, character):
        """This method turns a character's persona
        into a string for system instructions
        """
        try:
            return character.persona
        except Exception as e:
            return f"""You are {character.name}, a contestant on the
            reality TV show Survivor."""

    def get_memory(self, character):
        """This method turns a character's memories into a string 
        for system instructions
        """
        try:
            return character.memory
        except Exception as e:
            memory = f"""Your goal is to win Survivor.
              To do so, you need to decide who to vote for and convince other people to not vote for you.
              There are {len(self.game.characters)} people remaining: {[char.name for char in self.game.characters]}."""
            return memory

    def get_system_instructions(self, character):
        system_instructions = self.get_persona(character) + "\n" + self.get_memory(character) + "\n"
        system_instructions += (f"""You are in dialogue with:
                                {', '.join([x.name for x in self.participants if x.name != character.name])}.\n""")
        system_instructions +=(f"""When it's your turn to speak,
                                you can say something or walk away form the conversation.
                                If you say something, start with: '{character.name}says: '.
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
                "content": self.characters_system[character.name]
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
