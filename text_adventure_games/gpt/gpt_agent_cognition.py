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
from text_adventure_games.agent.cognition.reflect import build_observations_list

API_KEY = get_openai_api_key("Penn")
MODEL = 'gpt-4'


class ReflectionKani(Kani):
    system_reflection = """
    You will receive an enumerated list of observations that you have experienced in the last
    round of Survivor. Read these observations, identifying any commonalities between them. 
    You should then synthesize a {number} of reflections about the observations you have made. 
    Focus on generalizing the insights that can be gained from the information you have read.
"""
    
    def __init__(self, last_round_observations, system_prompt=system_reflection):
        self.last_round = last_round_observations
    
    async def get_prompt(self):
        if self.last_round:
            return await super.get_prompt() + ChatMessage.user(
                f"In the last round, you observed the following:\n{self.last_round}"
            )
    

#################################################
# Possible Kani implementation
#################################################
    
class AgentKani(Kani):  
    # includes static information about the character
    def __init__(self, persona):
        self.persona = persona
        self.agent_summary = ''
        # What world knowledge should be passed to the Kanis?
        self.world_info = ''
    # General Agent Actions could be routed to sub-Kanis
    # build system prompt with override get_prompt() asking Gpt4 

    def update_agent_summary(self, summary):
        self.agent_summary = summary

    def update_world_info(self, description):
        self.world_info = description
    
    # 1. Reflect: runs methods for generating reflective conclusions about past observations
    @ai_function
    def reflect(self, round):
        last_round_observations = build_observations_list(self.persona.memory, round, n=None)
        engine = OpenAIEngine(API_KEY, MODEL)
        reflection_ai = ReflectionKani(last_round_observations)
        # Needs to accomplish:
        # 1. From last n ObservationsNodes, generate 2 or 3 questions for further reflection
        #       - Alternative: directly synthesize k "reflections" from the last n Nodes
        # 2. Pass these to the MemoryStream as level 2 reflection type Nodes

    # 2. Act: Agent interacts with game state in some way; 
    #         probably via determination intent mechanism similar to HW2?
    @ai_function
    def act():
        engine = OpenAIEngine(key, model)
        action_ai = ActionKani()
        # Needs to accomplish:
        # 1. Select an action that aligns with Agent goals:
        #    Perhaps options include:
        #       - Dialogue
        #       - Interact with game state (pick up, move, etc)
        # 2. Execute the selected action

    # 3. Converse: logic for dialogue (continuation, exit, retreive relevant memories)
    @ai_function
    def converse():
        engine = OpenAIEngine(key, model)
        dialogue_ai = DialogueKani()
        # do stuff ...

    # 4. Plan: generate goals for variable time windows?
    @ai_function
    def plan():
        engine = OpenAIEngine(key, model)
        planning_ai = PlanningKani()
        # Needs to accomplish:
        # 1. Assessment of previous goals: accomplished or not?
        # 2. Creation of new goals given memory

    # 5. Perceive: gather new information available to this agent and store as new ObservationNodes
    # Though this may not actually require an LLM; just collection from the game history.        
    @ai_function
    def perceive():
        engine = OpenAIEngine(key, model)
        perception_ai = PerceivingKani()
        # do stuff

    # 6. Vote: special action that is triggered at the end of a round
    @ai_function
    def vote():
        engine = OpenAIEngine(key, model)
        voting_ai = VoterKani()