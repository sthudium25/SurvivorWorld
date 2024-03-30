"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent_cognition/impressions.py
Description: defines how agents store interpersonal impressions and theory-of-mind of other characters. 
             This assumes that "set_impression" will be called at least once at the end of a round.
             So, in the case that this agent has already made an impression about a person, only memories from 
             the last round should be reasoned over; other memories are theoretically already enocded in the agent's 
             impressions of the target.

             However, if a player comes across a new target, all relevant memories to the target will be pulled.

"""
from collections import defaultdict
from typing import TYPE_CHECKING, Dict
import json

# local imports
from text_adventure_games.agent.memory_stream import MemoryType
from text_adventure_games.assets.prompts import impressions_prompts as ip
from text_adventure_games.gpt.gpt_helpers import limit_context_length, gpt_get_action_importance
from text_adventure_games.utils.general import set_up_openai_client
from text_adventure_games.agent.agent_cognition import retrieve

if TYPE_CHECKING:
    from text_adventure_games.games import Game
    from text_adventure_games.things import Character

GPT4_MAX_TOKENS = 8192
IMPRESSION_MAX_OUTPUT = 512


class Impressions:

    def __init__(self):
        # keys are strings of the target agent "{name}_{id}"
        self.impressions = defaultdict()

    def get_impression(self, target: "Character"):
        return self.impressions.get(f"{target.name}_{target.id}", None)

    def set_impression(self, game: "Game", character: "Character", target: "Character"):
        """
        Create a 

        Args:
            game (Game): _description_
            character (Character): _description_
            target (Character): _description_
        """
        # get the agent's current impression of the target character
        target_impression = self.get_impression(target)
        
        # Get relevant memories 
        if target_impression:
            # keep nodes from the last round that mention the character's name
            memory_ids = character.memory.get_observations_by_round(game.round)
            nodes = [character.memory.get_observation(m_id) for m_id in memory_ids]
            context_list = [node.node_description for node in nodes if target.name in node.node_keywords]
            self.chronological = True
        else:
            # IF this agent has never reflected upon this target, get all relevant memories to them
            # TODO: how could this query be improved?
            # Relevant memories: least to most 
            context_list = retrieve.retrieve(game, 
                                             character, 
                                             n=-1, 
                                             query=f"I want to remember everything I know about {target.name}")
            self.chronological = False
        
        context_list = limit_context_length(context_list, 
                                            max_tokens=GPT4_MAX_TOKENS-IMPRESSION_MAX_OUTPUT,
                                            tokenizer=game.parser.tokenizer)
        
        impression = self.gpt_generate_impression(game, character, target.name, context_list, str(target_impression))

        self.impressions.update({f"{target.name}_{target.id}": impression})
  
    def gpt_generate_impression(self, 
                                game: "Game", 
                                character: "Character", 
                                target_name, 
                                memories, 
                                current_impression):
        client = set_up_openai_client("Helicone")

        system_prompt = ip.gpt_impressions_prompt.format(world_info=game.world_info,
                                                         persona_summary=character.persona.get_personal_summmary(),
                                                         target_name=target_name)
        
        user_prompt = self.build_user_message(target_name, memories, current_impression)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=IMPRESSION_MAX_OUTPUT,
            temperature=1,
            top_p=1,
        )

        impression = response.choices[0].message.content
        return impression

    def build_user_message(self, target_name, memories_list, current_impression):

        message = "Person: {t}\n\n".format(t=target_name)
        if self.chronological:
            ordering = "in chronological order"
        else:
            ordering = "in order from least to most relevant"

        message += "Current theory of mind for {t} {o}:\n{i}\n\n".format(t=target_name, o=ordering, i=current_impression)

        memory_str = "".join([f"{i}. {m}\n" for i, m in enumerate(memories_list)])
        message += "Memories to consider in developing a theory of mind for {t}:\n{m}".format(t=target_name, 
                                                                                              m=memory_str)
        
        return message
