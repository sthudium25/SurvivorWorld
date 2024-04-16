import tiktoken
from text_adventure_games.gpt.gpt_helpers import limit_context_length
from ..utils.general import set_up_openai_client
from ..agent.agent_cognition.retrieve import retrieve

GPT4_MAX_TOKENS = 8192
ACTION_MAX_OUTPUT = 100


class Dialogue:
    """This class handles dialogue happening between 2 or more characters.
    """

    def __init__(self, game, participants, command):
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
        self.dialogue_history = f'{command}. The dialogue just started.'
        for participant in self.participants:
            self.characters_system[participant.name] = self.get_system_instructions(participant)
        self.characters_mentioned = [character.name for character in self.participants]  # Characters mentioned so far in the dialogue

    def get_system_instructions(self, character):
        system_instructions = f"WORLD INFO: {self.game.world_info}" + "\n"
        system_instructions += f"You are {character.persona.summary}" + "\n"
        system_instructions += (f"""You are in dialogue with:
                                {', '.join([x.name for x in self.participants if x.name != character.name])}.\n""")
        system_instructions += (f"""When it's your turn to speak,
                                you can say something or walk away form the conversation.
                                If you say something, start with: '{character.name} says: '.
                                If you walk away, say only: '{character.name} leaves the conversation.'.
                                If you feel like the last two lines have not added new information
                                or people are speaking in circles, end the conversation.""")
        system_instructions += f"Your goals are: {character.goals}. " + "/n"
        reflections = character.impressions.get_multiple_impressions(self.game.characters.values())
        reflections = reflections[:2000]  # temporary fix to limit reflections
        system_instructions += f"REFLECTIONS ON OTHERS: {reflections}\n\n"
        system_instructions += "These are select MEMORIES in ORDER from LEAST to MOST RELEVANT: "
        query = f"""You are in dialogue with:
                                {', '.join([x.name for x in self.participants if x.name != character.name])}.\n
                    Your goals are: {character.goals}. """
        query += "\n" + self.dialogue_history.split("\n")[-1]
        context_list = retrieve(self.game, character, query, n=10)
        try:
            num_memories = len(context_list)  
        except Exception:
            num_memories = 0
        print(
            f"passing {num_memories} relevant memories to {character.name}")
        try:
            system_instructions += "".join([f"{m}\n" for m in context_list])
        except TypeError:
            system_instructions += "No memories. \n"
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
        i = 5  # Counter to avoid dialogue dragging on for too long
        while i > 0:
            for character in self.participants:
                # Get last line of dialogue and if any new characters are mentioned update system prompts
                last_line = self.dialogue_history.split("\n")[-1]
                keywords = self.game.parser.extract_keywords(last_line).get("characters", None)
                refresh_system_prompt = False
                if keywords:
                    for k in keywords:
                        if k not in self.characters_mentioned:
                            refresh_system_prompt = True
                if refresh_system_prompt:
                    for participant in self.participants:
                        self.characters_system[participant.name] = self.get_system_instructions(participant)
                
                # Get GPT response
                response = self.get_gpt_response(character)
                print(response)
                self.add_to_dialogue_history(response)

                # End conversation if a character leaves
                if response == f"{character.name} leaves the conversation.":
                    self.participants.remove(character)
                    print("The conversation is over")
                    break
            if self.is_dialogue_over():
                break
            i -= 1
        return self.dialogue_history
