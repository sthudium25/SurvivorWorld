"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: gpt_agent.py
Description: Methods that access the OPENAI API and make a call to GPT
"""

import asyncio
from typing import List
from kani import Kani, ai_function, ChatMessage
from kani.engines.openai import OpenAIEngine

# local imports
from ..utils.consts import get_openai_api_key
# from text_adventure_games.agent.cognition.reflect import build_observations_list

API_KEY = get_openai_api_key("Penn")
MODEL = 'gpt-4'

class AgentKani(Kani):
    # includes static information about the character
    def __init__(self, persona, name):
        self.persona = persona
        self.name = name
        # self.agent_summary = 
        # What world knowledge should be passed to the Kanis?
        self.world_info = 'You are in the world of Action Castle, a fantasy game.'
        self.system = "You are a delegating agent. You will receive information about a game environment and you must follow the instructions."
        self.perpetual = self.world_info + " Your name is" + self.name + '.'
        engine = OpenAIEngine(API_KEY, model=MODEL)
        super().__init__(engine, system_prompt=self.system, always_included_messages=self.perpetual)
    # General Agent Actions could be routed to sub-Kanis
    # build system prompt with override get_prompt() asking Gpt4 
        
    @ai_function
    async def act(self, loc_description):
        """
        Select an action that furthers the goals of the agent.
        """
        action_engine = OpenAIEngine(API_KEY, MODEL)

        # Need to figure out what to pass to this model as context
        # What portion of the AgentKanis chat history do we pass?
        action_ai = ActionKani(action_engine, system_prompt='', chat_history=self.chat_history)

        # TODO: Update this prompt to be more robust
        return await action_ai.chat_round_str("Given the context, choose an action...")
    
    def get_relevant_observations(self, lookups):
        # Keyword lookups: These should return ranked lists of observations
        # Ranking taking into account: recency, cosine similarity 
        for loc in lookups["location"]:
            loc_obs = self.persona.memory.get_obs_by_loc(loc)
        
        for character in lookups["characters"]:
            char_obs = self.persona.memory.get_obs_by_character(character)

        for item in lookups["items"]:
            item_obs = self.persona.memory.get_obs_by_item(item)


class ActionKani(Kani):
    pass
