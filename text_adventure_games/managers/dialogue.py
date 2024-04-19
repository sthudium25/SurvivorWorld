import tiktoken
from text_adventure_games.gpt.gpt_helpers import limit_context_length, get_prompt_token_count, GptCallHandler
from text_adventure_games.assets.prompts import dialogue_prompt as dp
from ..utils.general import set_up_openai_client
from ..agent.agent_cognition.retrieve import retrieve

ACTION_MAX_OUTPUT = 100


class Dialogue:
    """This class handles dialogue happening between 2 characters.
    """

    def __init__(self, game, participants, command):
        """
        Args:
            participants (List(Character)): sorted list of 
            characters by initiative.
        """

        self.game = game
        self.gpt_handler = self._set_up_gpt()
        self.token_offset = 0
        self.offset_pad = 5
        self.model_context_limit = self.gpt_handler.model_context_limit
        self.participants = participants
        self.characters_system = {}
        self.characters_user = {}
        self.participants_number = len(participants)
        self.dialogue_history = [f'{self.participants[0].name} wants to {command}. The dialogue just started.']

        # for every participant
        for participant in self.participants:
            # add them to the characters system dict using their name as the key
            self.characters_system[participant.name] = dict()
            self.characters_user[participant.name] = dict()

            # update this character's value – dictionary of each system instruction components
            # (intro, impressions, memories), where each is a key and the values are lists
            # containing the token count in the first index and the string representation in
            # the second.
            self.update_system_instruction(participant)
            self.update_user_instruction(participant,
                                         update_impressions=True,
                                         update_memories=True,
                                         system_instruction_token_count=self.get_system_instruction(participant)[0])

        # get a list of all characters in the conversation
        self.characters_mentioned = [character.name for character in self.participants]  # Characters mentioned so far in the dialogue

    def _set_up_gpt(self):
        model_params = {
            "api_key_org": "Helicone",
            "model": "gpt-4",
            "max_tokens": 250,
            "temperature": 1,
            "top_p": 1,
            "max_retries": 5
        }

        return GptCallHandler(**model_params) 

    def get_user_instruction(self, character):
        """
        This method gets the given character's user instruction token count and
        string representation.
        """

        # get this character's dictionary of system prompt components
        char_inst_comp = self.characters_user[character.name]

        # return a tuple containing the system instructions token count and string representation
        return (char_inst_comp['impressions'][0] + char_inst_comp['memories'][0] + char_inst_comp['dialogue_history'][0],
                char_inst_comp['impressions'][1] + char_inst_comp['memories'][1] + char_inst_comp['dialogue_history'][1])

    def get_system_instruction(self, character):
        """
        This method gets the given character's system instruction token count and
        string representation.
        """

        # get this character's dictionary of system prompt components
        char_inst_comp = self.characters_system[character.name]

        # return a tuple containing the system instructions token count and string representation
        return (char_inst_comp['intro'][0],
                char_inst_comp['intro'][1])

    def update_user_instruction(self, character, update_impressions=False, update_memories=False,
                                 system_instruction_token_count=0):
        """This method constructs and updates the user instructions which include
        the impressions, the memory and the dialog history.
        Currently, the impressions are also passed in without being shortened. The memories are
        reduced if necessary to fit into GPT's context. Note that these aren't returned, but
        rather are stored in the characters system dictionary as a dictionary of lists.
        Each component serves as a dictionary key, and its value is a list where the first
        index is the component's token count and the second is its string representation.

        Args:
            character (_type_): _description_
            impressions (bool, optional): _description_. Defaults to True.
            memories (bool, optional): _description_. Defaults to True.
        """

        ### IMPRESSIONS OF OTHER CHARACTERS###
        if update_impressions:
            # get impressions of the other game characters
            impressions = character.impressions.get_multiple_impressions(self.game.characters.values())
            impressions = "YOUR IMPRESSIONS OF OTHERS:\n" + "\n".join(impressions) + "\n\n"

            # get the impressions token count
            impressions_token_count = get_prompt_token_count(content=impressions, role=None, pad_reply=False)

            # update the character's impressions in the characters system dictionary
            self.characters_user[character.name]['impressions'] = (impressions_token_count, impressions)

        ### MEMORIES OF CHARACTERS IN DIALOGUE/MENTIONED ###

        # if updating the memories
        if update_memories:

            # make a memory retrieval query based on characters partaking/mentioned in this conversation
            query = ''.join(["You are in dialogue with: ",
                            ', '.join([x.name for x in self.participants if x.name != character.name])+'.\n',
                            f"Your goals are: {character.goals.get_goals(round=(self.game.round-1), as_str=True)}\n"])
            query += self.dialogue_history[-1]

            # get the 25 most recent/relevant/important memories
            context_list = retrieve(self.game, character, query, n=25)

            # if there are memories to include in the system prompt
            if context_list:

                # include primer message at 0th index in list
                context_list = ["These are select MEMORIES in ORDER from MOST to LEAST RELEVANT:\n"] + list(reversed(context_list))

                impressions_token_count = self.characters_user[character.name]['impressions'][0]

                # limit memories to fit in GPT's context by trimming less recent/relevant/important memories
                memories_limited = limit_context_length(history=context_list,
                                                        max_tokens=self.model_context_limit - impressions_token_count,
                                                        keep_most_recent=False)

                # convert the list of limited memories into a single string
                memories_limited_str = "".join([f"{m}\n" for m in memories_limited])

                # get the limited memories token count
                memories_limited_token_count = get_prompt_token_count(content=memories_limited_str, role=None, pad_reply=False)

                # update the character's memories in the characters system dictionary
                self.characters_user[character.name]['memories'] = (memories_limited_token_count, memories_limited_str)
            
            else:
                self.characters_user[character.name]['memories'] = (2, "No memories")

        # update dialogue history
        # limit the number of dialogue messages (if necessary, trimming from the start) to fit into GPT's context
        limited_dialog = limit_context_length(history=self.get_dialogue_history_list(),
                                              max_tokens=self.model_context_limit-system_instruction_token_count-self.gpt_handler.max_tokens)

        # get the limited dialogue as a string
        dialog_str = '\n'.join(limited_dialog)

        # update the dialog history with the current token count being passed to GPT
        dialogue_history_token_count = get_prompt_token_count(content=dialog_str, role=None, pad_reply=False)

        dialogue_history_prompt = dp.gpt_dialogue_user_prompt.format(character=character.name,
                                                                     dialogue_history=dialog_str)
        
        self.characters_user[character.name]['dialogue_history'] = (dialogue_history_token_count, dialogue_history_prompt)

    def update_system_instruction(self, character):
        """
        This method constructs and updates the system instructions which now only includes the intro (updated).
        The intro must be included without trimming.
        Each component serves as a dictionary key, and its value is a list where the first
        index is the component's token count and the second is its string representation.

        Args:
            character (Character): the character whose system instructions are
                                   being retrieved
            intro (bool): if True, this recalculates the intro part of the
                          prompt - both its token count and string
            impressions (bool): if True, this recalculates the impressions part
                                of the prompt - both its token count and string
            memories (bool): if True, this recalculates the memories part of
                             the prompt - both its token count and string

        Raises:
            TypeError: _description_
        """

        ### REQUIRED START TO SYSTEM PROMPT (CAN'T TRIM) ###
        intro = character.get_standard_info(self.game)
        
        # add dialogue instructions
        other_character = ', '.join([x.name for x in self.participants if x.name != character.name])
        intro += dp.gpt_dialogue_system_prompt.format(other_character=other_character)

        # get the system prompt intro token count
        intro_token_count = get_prompt_token_count(content=intro, role='system', pad_reply=False)

        # account for the number of tokens in the resulting role (just the word 'user'),
        # including a padding for GPT's reply containing <|start|>assistant<|message|>
        intro_token_count += get_prompt_token_count(content=None, role='user', pad_reply=True)

        # update the character's intro in the characters system dictionary
        self.characters_system[character.name]['intro'] = (intro_token_count, intro)
        
    def get_dialogue_history_list(self):
        return self.dialogue_history
    

    def get_dialogue_history(self):
        return '\n'.join(self.dialogue_history)


    def add_to_dialogue_history(self, message):
        self.dialogue_history.append(message)


    def get_gpt_response(self, character):
        """
        This method makes the call to GPT to get a character's dialog response
        based on their stored system prompt in characters system as well as
        the dialogue history, which is included as a user message. 

        Args:
            character (Character): the character whose system instructions are
                                   being retrieved

        Raises:
            Exception: _description_
        """

        # Get the system instruction token count and string representation.
        # To change this, pass in True to any system prompt components that we want to update
        system_instruction_token_count, system_instruction_str = self.get_system_instruction(character=character)
        user_instruction_token_count, user_instruction_str = self.get_user_instruction(character=character)

        # if the sum of the system prompt and dialogue history token counts exceeds the max tokens
        if system_instruction_token_count + user_instruction_token_count >= self.model_context_limit:

            # reduce the max token count by the dialogue count, and reduce the number of memories included in the prompt
            self.model_context_limit = self.model_context_limit - user_instruction_token_count
            self.update_user_instruction(character,
                                         update_impressions=False,
                                         update_memories=True,
                                         system_instruction_token_count=system_instruction_token_count)
            system_instruction_token_count, system_instruction_str = self.get_system_instruction(character=character,
                                                                                                 memories=True)

        # get GPT's response
        response = self.gpt_handler.generate(
            system=system_instruction_str,
            user=user_instruction_str
        )

        if isinstance(response, tuple):
            print("Bad Request Error")
            # This occurs when there was a Bad Request Error cause for exceeding token limit
            success, token_difference = response
            # Add this offset to the calculations of token limits and pad it 
            self.token_offset = token_difference + self.offset_pad
            self.offset_pad += 2 * self.offset_pad 
            return self.get_gpt_response(character)

        return response

    def is_dialogue_over(self):
        if len(self.participants) <= 1:
            return True
        return False

    def dialogue_loop(self):
        i = 10  # Counter to avoid dialogue dragging on for too long
        print("Dialogue started succesfully")
        while i > 0:
            for character in self.participants:
                # Get last line of dialogue and if any new characters are mentioned update system prompts
                last_line = self.dialogue_history[-1]
                keywords = self.game.parser.extract_keywords(last_line).get("characters", None)
                update_memories = False
                if keywords:
                    for k in keywords:
                        if k not in self.characters_mentioned:
                            update_memories = True

                self.update_user_instruction(character,
                                             update_impressions=False,
                                             update_memories=update_memories,
                                             system_instruction_token_count=self.get_system_instruction(character)[0])
                # Get GPT response
                response = self.get_gpt_response(character)
                response = f"{character.name} said: " + response
                print(response)
                self.add_to_dialogue_history(response)

                # update the dialog history token count with the latest reply
                # response_token_count = get_prompt_token_count(content=response, role=None, pad_reply=False)
                # self.dialogue_history_token_count += response_token_count

                # End conversation if a character leaves
                if "I leave the conversation" in response:
                    self.participants.remove(character)
                    print("The conversation is over")
                    break
            if self.is_dialogue_over():
                break
            i -= 1
        return self.dialogue_history