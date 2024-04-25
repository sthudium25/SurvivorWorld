"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent_cognition/impressions.py
Description: defines how agents store interpersonal impressions and theory-of-mind of other characters. 
             This assumes that "set_impression" will be called at least once at the end of a round.
             So, in the case that this agent has already made an impression about a person, only memories from 
             the last round should be reasoned over; other memories are theoretically already encoded in the agent's 
             impressions of the target.

             However, if a player comes across a new target, all relevant memories to the target will be pulled.

"""
from collections import defaultdict
from typing import TYPE_CHECKING

# local imports
from text_adventure_games.assets.prompts import impressions_prompts as ip
from text_adventure_games.gpt.gpt_helpers import (limit_context_length, 
                                                  get_token_remainder,
                                                  get_prompt_token_count,
                                                  context_list_to_string, 
                                                  GptCallHandler)
from text_adventure_games.agent.agent_cognition import retrieve

if TYPE_CHECKING:
    from text_adventure_games.games import Game
    from text_adventure_games.things import Character

IMPRESSION_MAX_OUTPUT = 512


class Impressions:

    def __init__(self, name, id):
        """
        Structure of this dict is:
        top level keys are strings of the target agent "{name}_{id}"
        The inner dict contains the "impression": text describing the agent's impression of a target agent, 
                                    "round": round in which the impression was made,  # probably mostly for logging?
                                    "tick": tick on which the impression was made,  # probably mostly for logging?
                                    "creation": the total ticks at time of creation.

        Args:
            name (str): _description_
            id (int): _description_
        """
        
        self.impressions = defaultdict(dict)
        self.name = name
        self.id = id
        self.last_target = None

        # GPT Call handler attrs
        self.gpt_handler = self._set_up_gpt()
        self.token_offset = 50  # Taking into account a few variable tokens in the user prompt
        self.offset_pad = 5
 
    def _set_up_gpt(self):
        model_params = {
            "api_key_org": "Helicone",
            "model": "gpt-4",
            "max_tokens": IMPRESSION_MAX_OUTPUT,
            "temperature": 1,
            "top_p": 1,
            "max_retries": 5
        }

        return GptCallHandler(**model_params)

    def _get_impression(self, target: "Character", str_only=True):
        """
        Get impressions of a target character

        Args:
            target (Character): the target requested

        Returns:
            str: the text of the impression
        """
        impression = self.impressions.get(f"{target.name}_{target.id}", None)
        if impression and str_only:
            return impression["impression"]
        elif impression and not str_only:
            return impression
        else:
            return None
    
    def get_multiple_impressions(self, character_list) -> list:
        """
        Get impressions of several characters.

        Args:
            character_list (list[Character]): a list of character objects

        Returns:
            list: concatenated impressions of the requested characters
        """
        char_impressions = []
        for char in character_list:
            if char.id == self.id:
                continue
            char_impression = f"Your theory of mind of and relationship with {char.name}:\n"
            char_impression += self._get_impression(char) or "None\n"
            char_impressions.append(char_impression)
        return char_impressions
    
    def update_impression(self, game: "Game", character: "Character", target: "Character") -> None:
        """
        Conditionally triggers an update of a character's impression of a target.
        Simple heuristic: if the age is greater than max_ticks_per_round, then this impression should be updated.

        Also, if no impression has been made yet then one should be made.

        Args:
            game (Game): the current game object
            character (Character): the agent making the impression
            target (Character): the target character of the impression

        Returns:
            None
        """
        total_ticks = game.total_ticks
        should_update = False
        impression = self._get_impression(target, str_only=False)
        if not impression:
            should_update = True
        else:
            impression_age = impression["creation"]
            if (total_ticks - impression_age) > game.max_ticks_per_round:
                should_update = True
        # Don't make an impression until half a round has passed
        if should_update and total_ticks > game.max_ticks_per_round / 2:
            self.set_impression(game, character, target)

    def set_impression(self, game: "Game", character: "Character", target: "Character") -> None:
        """
        Create an impression of a character.

        Args:
            game (Game): the game
            character (Character): the agent making the impression
            target (Character): the target character of the impression
        
        Returns:
            None
        """
        self.last_target = target
        system, user = self.build_impression_prompts(game, character, target)

        impression = self.gpt_generate_impression(system, user)
        # print(f"{character.name} impression of {target.name}: {impression}")

        self.impressions.update({f"{target.name}_{target.id}": {"impression": impression,
                                                                "round": game.round,
                                                                "tick": game.tick,
                                                                "creation": game.total_ticks}})
  
    def gpt_generate_impression(self, 
                                system_prompt,
                                user_prompt) -> str:
        """
        Call to GPT to create a new impression of the target character.
        System prompt uses: world info, agent personal summary, and the target's name
        User prompt uses: target's name, a list of memories about the target, and the existing impression of the target.

        Args:
            game (Game): the game
            character (Character): the character creating the impression
            target_name (str): the name of the target of the impression
            memories (list): a list of memory strings
            current_impression (str): the existing impression of the target

        Returns:
            str: a new or updated impression
        """
        impression = self.gpt_handler.generate(system=system_prompt, user=user_prompt)
        if isinstance(impression, tuple):
            # This occurs when there was a Bad Request Error cause for exceeding token limit
            success, token_difference = impression
            # Add this offset to the calculations of token limits and pad it 
            self.token_offset = token_difference + self.offset_pad
            self.offset_pad += 2 * self.offset_pad 
            return self.set_impression(self.game, self.character, self.last_target)
        
        return impression

    def build_impression_prompts(self, game, character, target):
        system_prompt, sys_token_count = self.build_system_prompt(game, character, target.name)
        consumed_tokens = sys_token_count + self.token_offset
        
        user_prompt = self.build_user_message(game, character, target, consumed_tokens=consumed_tokens)
        return system_prompt, user_prompt
    
    def build_system_prompt(self, game, character, target_name):
        system_prompt = character.get_standard_info(game, include_perceptions=False)
        system_prompt += ip.gpt_impressions_prompt.format(target_name=target_name)
        sys_tkn_count = get_prompt_token_count(system_prompt)
        return system_prompt, sys_tkn_count

    def build_user_message(self, game, character, target, consumed_tokens=0) -> str:
        """
        Helper method to build out the user message string for impression prompting.

        Args:
            target_name (str): name of the target
            memories_list (list): list of relevant memories
            current_impression (str): the existing impression of the character

        Returns:
            str: _description_
        """
        # get the agent's current impression of the target character
        target_impression = self._get_impression(target)

        # Get relevant memories 
        if target_impression:
            # keep nodes from the last round that mention the character's name
            memory_ids = character.memory.get_observations_by_round(game.round)
            nodes = [character.memory.get_observation(m_id) for m_id in memory_ids]
            context_list = [node.node_description for node in nodes if target.name in node.node_keywords]
            self.chronological = True
            target_impression_tkns = get_prompt_token_count(target_impression)
        else:
            # IF this agent has never reflected upon this target, get the 10 most relevant memories about them
            # TODO: how could this query be improved?
            # Relevant memories: least to most 
            context_list = retrieve.retrieve(game, 
                                             character, 
                                             n=-1, 
                                             query=f"I want to remember everything I know about {target.name}")
            self.chronological = False
            target_impression_tkns = 0
        
        available_tokens = get_token_remainder(self.gpt_handler.model_context_limit,
                                               consumed_tokens,
                                               target_impression_tkns, 
                                               self.gpt_handler.max_tokens  # Max output tokens set by user
                                               )
        if context_list:
            context_list = limit_context_length(context_list, 
                                                max_tokens=available_tokens,
                                                tokenizer=game.parser.tokenizer)

        message = "Target person: {t}\n\n".format(t=target.name)
        if self.chronological:
            ordering = "in chronological order"
        else:
            ordering = "in order from least to most relevant"

        if target_impression:
            message += "Current theory of mind for {t} {o}:\n{i}\n\n".format(t=target.name, o=ordering, i=target_impression)
        if context_list:
            memory_str = context_list_to_string(context_list, sep="\n")
            message += "Memories to consider in developing a theory of mind for {t}:\n{m}".format(t=target.name, 
                                                                                                  m=memory_str)
        
        return message
