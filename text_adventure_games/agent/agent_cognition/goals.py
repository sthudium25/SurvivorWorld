"""
Author: Rut Vyas

File: agent_cognition/goals.py
Description: defines how agents reflect upon their past experiences
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from collections import defaultdict
from text_adventure_games.utils.general import set_up_openai_client
from text_adventure_games.assets import goal_prompt

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

        # retrieving apt reflection nodes
        reflection_raw = []
        node_ids = self.character.memory.get_observations_by_round(game.round)
        for node_id in node_ids:
            node = self.character.memory.get_observation(node_id)
            if node.node_type.value == 3:
                reflection_raw.append(node.node_description)
        reflection = " ".join(reflection_raw)

        # get all character objects
        char_objects = []
        for char in game.characters:
            char_objects.append(char)
        
        impressions_str = self.character.impressions.get_multiple_impression(char_objects)
        user_prompt = {"Reflection of previous round: \n{ref} \n\n Impressions: \n{imp}"}.format(ref=reflection,
                                                                                                 imp=impressions_str)
        
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
        # for experimentation purposes
        self.goal_update(goal, game)
        return goal
    
    def goal_update(self, goal: str, game: "Game"):
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

    # def evaluate_goals(game: "Game", character: "Character"):
    #  #TODO : Separate file with other evalaution - maybe create a new module
    #  pass
