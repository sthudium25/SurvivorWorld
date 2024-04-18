import tiktoken
from text_adventure_games.gpt.gpt_helpers import limit_context_length, get_prompt_token_count
from text_adventure_games.assets.prompts import dialogue_prompt as dp
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
        self.max_tokens = GPT4_MAX_TOKENS-self.max_output_tokens  # GPT-4's max total tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.game = game
        self.participants = participants
        self.characters_system = {}
        self.participants_number = len(participants)
        self.dialogue_history = [f'{command}. The dialogue just started.']
        self.dialogue_history_token_count = get_prompt_token_count(content=self.dialogue_history, role=None, pad_reply=False)

        # for every participant
        for participant in self.participants:
            # add them to the characters system dict using their name as the key
            self.characters_system[participant.name] = dict()

            # update this character's value – dictionary of each system instruction components
            # (intro, impressions, memories), where each is a key and the values are lists
            # containing the token count in the first index and the string representation in
            # the second.
            self.get_system_instruction_components(participant, intro=True, impressions=True, memories=True)

        # get a list of all characters in the conversation
        self.characters_mentioned = [character.name for character in self.participants]  # Characters mentioned so far in the dialogue


    def get_system_instruction(self, character, intro=False, impressions=False, memories=False):
        """
        This method gets the given character's system instruction token count and
        string representation.

        Args:
            character (Character): the character whose system instructions are
                                   being retrieved
            intro (bool): if True, this recalculates the intro part of the
                          prompt - both its token count and string
            impressions (bool): if True, this recalculates the impressions part
                                of the prompt - both its token count and string
            memories (bool): if True, this recalculates the memories part of
                             the prompt - both its token count and string

        Returns:
            tuple (int, str): the integer refers to the system instruction
                              token count and the string refers to the
                              actual instructions
        """

        # update the system instructions components for any set to True
        self.get_system_instruction_components(character=character,
                                               intro=intro,
                                               impressions=impressions,
                                               memories=memories)

        # get this character's dictionary of system prompt components
        char_inst_comp = self.characters_system[character.name]

        char_intro = char_inst_comp['intro'][1]
        char_impressions = char_inst_comp['impressions'][1] 
        char_memories = char_inst_comp['memories'][1]

        # return a tuple containing the system instructions token count and string representation
        return (char_inst_comp['intro'][0] + char_inst_comp['impressions'][0] + char_inst_comp['memories'][0],
                char_inst_comp['intro'][1] + char_inst_comp['impressions'][1] + char_inst_comp['memories'][1])


    def get_system_instruction_components(self, character, intro=True, impressions=True, memories=True):
        """
        This method constructs and updates the system instructions which are broken down into
        intro, impressions, and memories components. The intro must be included without trimming.
        Currently, the impressions are also passed in without being shortened. The memories are
        reduced if necessary to fit into GPT's context. Note that these aren't returned, but
        rather are stored in the characters system dictionary as a dictionary of lists.
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

        # if updating the intro
        if intro:
            
            # make the system instructions intro including world info, persona summary and goals
            intro = ''.join([f"WORLD INFO: {self.game.world_info}\n",
                             f"You are {character.persona.summary}\n"])
            
            intro += f"Your goals are: {character.goals.get_goals(as_str=True)}\n"
            
            # add dialogue instructions
            other_character = ', '.join([x.name for x in self.participants if x.name != character.name])
            intro += dp.gpt_dialogue_prompt.format(character=character.name,
                                                   other_character=other_character)

            # get the system prompt intro token count
            intro_token_count = get_prompt_token_count(content=intro, role='system', pad_reply=False)

            # account for the number of tokens in the resulting role (just the word 'user'),
            # including a padding for GPT's reply containing <|start|>assistant<|message|>
            intro_token_count += get_prompt_token_count(content=None, role='user', pad_reply=True)

            # update the character's intro in the characters system dictionary
            self.characters_system[character.name]['intro'] = (intro_token_count, intro)


        ### IMPRESSIONS OF OTHER CHARACTERS (REMOVE TRIBAL COUNCIL MEMBERS?) ###

        # if updating the impressions
        if impressions:

            # get impressions of the other game characters
            impressions = character.impressions.get_multiple_impressions(self.game.characters.values())
            impressions = "IMPRESSIONS OF OTHERS:\n" + impressions + "\n\n"

            # get the impressions token count
            impressions_token_count = get_prompt_token_count(content=impressions, role=None, pad_reply=False)

            # update the character's impressions in the characters system dictionary
            self.characters_system[character.name]['impressions'] = (impressions_token_count, impressions)


        ### MEMORIES OF CHARACTERS IN DIALOGUE/MENTIONED ###

        # if updating the memories
        if memories:

            # make a memory retrieval query based on characters partaking/mentioned in this conversation
            query = ''.join(["You are in dialogue with: ",
                            ', '.join([x.name for x in self.participants if x.name != character.name])+'.\n',
                            "Your goals are: {character.goals}\n"])
            query += self.dialogue_history[-1]

            # get the 25 most recent/relevant/important memories
            context_list = retrieve(self.game, character, query, n=25)

            # if there are memories to include in the system prompt
            if context_list:

                # include primer message at 0th index in list
                context_list = ["These are select MEMORIES in ORDER from MOST to LEAST RELEVANT:\n"] + list(reversed(context_list))

                intro_token_count = self.characters_system[character.name]['intro'][0]
                impressions_token_count = self.characters_system[character.name]['impressions'][0]

                # limit memories to fit in GPT's context by trimming less recent/relevant/important memories
                memories_limited = limit_context_length(history=context_list,
                                                        max_tokens=self.max_tokens - intro_token_count - impressions_token_count,
                                                        keep_most_recent=False)

                ## I don't think we need to utilize a try-except block here
                # try:
                #     print(f"passing {len(memories_limited)} relevant memories to {character.name}")
                # except Exception:
                #     pass

                # print(f"passing {max(0, len(memories_limited)-1)} relevant memories to {character.name}")

                # I'm also not sure we need a try-exept here, but I'm leaving it for now
                # convert the list of limited memories into a single string
                try:
                    memories_limited_str = "".join([f"{m}\n" for m in memories_limited])
                except TypeError:
                    pass

                # get the limited memories token count
                memories_limited_token_count = get_prompt_token_count(content=memories_limited_str, role=None, pad_reply=False)

                # update the character's memories in the characters system dictionary
                self.characters_system[character.name]['memories'] = (memories_limited_token_count, memories_limited_str)
            
            else:
                # if no memories, add a "no memories" string 
                self.characters_system[character.name]['memories'] = (2, "No memories")
    

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
        # Currently, we are not updating any of the system prompt when no new characters are mentioned.
        # To change this, pass in True to any system prompt components that we want to update
        system_instruction_token_count, system_instruction_str = self.get_system_instruction(character=character)

        # if the sum of the system prompt and dialogue history token counts exceeds the max tokens
        if system_instruction_token_count + self.dialogue_history_token_count >= self.max_tokens:

            # reduce the max token count by the dialogue count, and reduce the number of memories included in the prompt
            self.max_tokens = GPT4_MAX_TOKENS - self.max_output_tokens - self.dialogue_history_token_count
            system_instruction_token_count, system_instruction_str = self.get_system_instruction(character=character, memories=True)

        # limit the number of dialogue messages (if necessary, trimming from the start) to fit into GPT's context
        limited_dialog = limit_context_length(history=self.get_dialogue_history_list(),
                                              max_tokens=GPT4_MAX_TOKENS-system_instruction_token_count-self.max_output_tokens)

        # get the limited dialogue as a string
        dialog_str = '\n'.join(limited_dialog)

        # update the dialog history with the current token count being passed to GPT
        self.dialogue_history_token_count = get_prompt_token_count(content=dialog_str, role=None, pad_reply=False)

        # try getting GPT's response
        try:
            messages = [{
                "role": "system",
                "content": system_instruction_str
            },
                {
                "role": "user",
                "content": dialog_str
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
                last_line = self.dialogue_history[-1]
                keywords = self.game.parser.extract_keywords(last_line).get("characters", None)
                refresh_system_prompt = False
                if keywords:
                    for k in keywords:
                        if k not in self.characters_mentioned:
                            refresh_system_prompt = True
                if refresh_system_prompt:
                    for participant in self.participants:
                        self.get_system_instruction_components(participant,
                                                                intro=True,
                                                                impressions=True,
                                                                memories=True)
                
                # Get GPT response
                response = self.get_gpt_response(character)
                print(response)
                self.add_to_dialogue_history(response)

                # update the dialog history token count with the latest reply
                response_token_count = get_prompt_token_count(content=response, role=None, pad_reply=False)
                self.dialogue_history_token_count += response_token_count

                # End conversation if a character leaves
                if response == f"{character.name} leaves the conversation.":
                    self.participants.remove(character)
                    print("The conversation is over")
                    break
            if self.is_dialogue_over():
                break
            i -= 1
        return self.dialogue_history