import tiktoken
from openai import OpenAI


class Dialogue:
    """This class handles dialogue happening between 2 or more characters.
    """

    def __init__(self, participants):
        """
        Args:
            participants (List(Character)): sorted list of characters by initiative.
        """
        self.verbose = False
        self.client = OpenAI(base_url="https://oai.hconeai.com/v1",
                             api_key="sk-helicone-cp-esmpxtq-jpjevdq-q5w4saq-wwfbntq",)
        self.gpt_model = "gpt-4"
        self.max_output_tokens = 256 # You get to pick this
        self.max_tokens = 8192-self.max_output_tokens # GPT-4's max total tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.participants = participants
        self.characters_system = {}
        self.participants_number = len(participants)
        self.dialogue_history = []
        self.dialogue_history.append({'character': 'narrator',
                                      'content': 'The dialogue just started.'})
        self.max_tokens = 1000
        for participant in self.participants:
            self.characters_system[participant.name] = self.get_system_instructions(participant)

    def get_persona(self, character):
        """This method turns a character's persona into a string for system instructions
        """
        try:
            return character.persona
        except Exception as e:
            return f"You are {character.name}, a contestant on the reality TV show Survivor."

    def get_memory(self, character):
        """This method turns a character's memories into a string for system instructions
        """
        try:
            return character.memory
        except Exception as e:
            return "Your goal is to win Survivor. To do so, you need to decide who to vote for and convince other people to not vote for you. There are 5 people remaining: Josh, Tom, Alex, Jennifer and Chiara."
    
    def get_system_instructions(self, character):
        system_instructions = self.get_persona(character) + "\n" + self.get_memory(character) + "\n"
        system_instructions += (f"You are in dialogue with: {', '.join([x.name for x in self.participants if x.name != character.name])}.\n")
        system_instructions +=(f"When it's your turn to speak, you can say something, stay silent, or walk away form the conversation. If you say something, start with: '{character.name}says: '")
        return system_instructions
    
    def get_character_perspective(self, character):
        character_perspective = []
        for line in self.dialogue_history:
            if line["character"] == character.name:
                character_perspective.append({"role": "assistant",
                                              "content": line["content"]})
            else:
                character_perspective.append({"role": "user",
                                              "content": line["content"]})
        return character_perspective

    def add_to_dialogue_history(self, message, character):
        content = {"character": character.name,
                   "content": message}
        self.dialogue_history.append(content)

    def get_gpt_response(self, character):
        try:
            messages = [{
                "role": "system",
                "content": self.characters_system[character.name]
            }]
            context = self.get_character_perspective(character)
            messages.extend(context)
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
        i = 0
        while i < 10:
            for character in self.participants:
                response = self.get_gpt_response(character)
                print(response)
                self.add_to_dialogue_history(response, character)
                if response == f"{character.name} leaves the conversation.":
                    self.participants.pop(character)
            if self.is_dialogue_over():
                print("The conversation is over")
                break
            i += 1
