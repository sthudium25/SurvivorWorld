"""
Author: Rut Vyas

File: agent_cognition/goals.py
Description: defines how agents reflect upon their past experiences
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from collections import defaultdict

import numpy as np
from text_adventure_games.utils.general import set_up_openai_client, get_text_embedding
from text_adventure_games.assets.prompts import goal_prompt

if TYPE_CHECKING:
    from text_adventure_games.things.characters import Character
    from text_adventure_games.games import Game

GPT4_MAX_TOKENS = 8192

# 1. Get character's goals
# 2. Obtain a list of memories
# 3. ask 

# TODO: max output length ? - TBD
# TODO: summarize impressions for goals ? - TBD
# TODO: pass previous round plan - try passing in system prompt - try on playground first

class Goals:

    def __init__(self, character: "Character"):
        """
        The goal is stored in the form of a dictionary based on the priority with the round number as the key in the following format:
            {Round #: 
                {"Low Priority": _description_,
                 "Medium Priority: _description_,
                 "High Priority": _description_} 
        """
        self.character = character
        self.goals = defaultdict(dict)
        self.goal_embeddings = defaultdict(np.ndarray)

    def gpt_generate_goals(self, game: "Game") -> str:
        """
        Calls GPT to create a goal for the character
        System prompt uses: world info, agent personal summary, and the target's name
        User prompt uses: impressions created by this character of other players, reflection of previous round

        Args:
            game (Game): the game
            character (Character): the character creating the impression

        Returns:
            str: a new goal for this round
        """
        client = set_up_openai_client("Helicone")

        system_prompt = goal_prompt.gpt_goals_prompt.format(world_info=game.world_info, 
                                                            persona_summary=self.character.persona.summary)

        user_prompt = self.build_user_prompt(game)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
       
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            # max_tokens=IMPRESSION_MAX_OUTPUT,
            temperature=1,
            top_p=1)
        
        goal = response.choices[0].message.content
        
        # get embedding of goal
        goal_embed = self._create_goal_embedding(goal)
        # for experimentation purposes
        self.goal_update(goal, goal_embed, game)
        return goal
    
    def build_user_prompt(self, game):
        # retrieving apt reflection nodes
        reflection_raw = []
        node_ids = self.character.memory.get_observations_by_round(game.round)
        for node_id in node_ids:
            node = self.character.memory.get_observation(node_id)
            if node.node_type.value == 3:
                reflection_raw.append(node.node_description)
        reflection = "\n".join(reflection_raw)

        # get all character objects
        char_objects = list(game.characters.values())
        
        if self.character.use_impressions:
            impressions_str = self.character.impressions.get_multiple_impressions(char_objects)
        else:
            impressions_str = None

        user_prompt = "Additional context for creating your goal:\n"
        if reflection:
            user_prompt += f"Reflections on this round:\n{reflection}\n\n"
        if impressions_str:
            user_prompt += f"Impressions: \n{impressions_str}\n"
        user_prompt += "If you want to update your goals, do so now."
        return user_prompt
    
    def goal_update(self, goal: str, goal_embedding: np.ndarray, game: "Game"):
        """
        Maintains the dictionary of goals for the character by round
        """
        round = game.round
        self.goals[round] = {}
        for line in goal.split('\n'):
            if 'Low Priority' in line:
                self.goals[round]['Low Priority:'] = line.replace('Low Priority: ', '')
            elif 'Medium Priority' in line:
                self.goals[round]['Medium Priority:'] = line.replace('Medium Priority: ', '')
            elif 'High Priority' in line:
                self.goals[round]['High Priority:'] = line.replace('High Priority: ', '')
        self.goal_embeddings.update({round: goal_embedding})
        self.update_goals_in_memory(round)

    def get_goals(self, round=-1, priority="all"):
        """
        Getter function for goal
            Args:
                round: round number (default is all rounds)
                priority: priority of goal needed (default is all priority goals)

            Returns:
                The goal
        """
        if round != -1 and priority != "all":
            return self.goals[round][priority]
        elif round != -1 and priority == "all":
            return self.goals[round]
        else:
            return self.goals
        
    def _create_goal_embedding(self, goal: str) -> np.ndarray:
        goal_embedding = get_text_embedding(goal)
        return goal_embedding

    def get_goal_embedding(self, round: int):
        return self.goal_embeddings.get(round, None)
    
    def update_goals_in_memory(self, round):
        curr_embedding = self.get_goal_embedding(round)
        if curr_embedding:
            self.character.memory.set_goal_query(curr_embedding)

    # def evaluate_goals(game: "Game", character: "Character"):
    #  #TODO : Separate file with other evalaution - maybe create a new module
    #  pass
