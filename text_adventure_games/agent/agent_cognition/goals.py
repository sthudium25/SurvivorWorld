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
        self.goal_scores = defaultdict(dict)
        self.recent_reflection = None
        self.goal_embeddings = defaultdict(np.ndarray)

    def gpt_generate_goals(self, game: "Game") -> str:
        """
        Calls GPT to create a goal for the character
        System prompt uses: world info, agent personal summary, and the target's name
        User prompt uses: impressions created by this character of other players, reflection of previous round

        Args:
            game (Game): the game

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

        #retreive goals and scores for prev round and two rounds prior
        round = game.round
        if round > 1:
            goal_prev = self.get_goals(round = round-1)
            score = self.get_goal_scores(round = round-1)
        if round > 2:
            goal_prev_2 = self.get_goals(round = round-2)
            score_2 = self.get_goal_scores(round = round-2)
        
        #retreive refelction nodes for two rounds prior
        reflection_raw_2 = []
        node_ids = self.character.memory.get_observations_by_round(round-2)
        for node_id in node_ids:
            node = self.character.memory.get_observation(node_id)
            if node.node_type.value == 3:
                reflection_raw_2.append(node.node_description)
        reflection_2 = "\n".join(reflection_raw_2)

        # get all character objects
        # char_objects = list(game.characters.values())
        
        # if self.character.use_impressions:
        #     impressions_str = self.character.impressions.get_multiple_impressions(char_objects)
        # else:
        #     impressions_str = None

        user_prompt = "Additional context for creating your goal:\n"
        if self.recent_reflection is not None:
            user_prompt += f"Reflections on prior round:\n{self.recent_reflection}\n\n"
            user_prompt += f"Reflections on two rounds prior:\n{reflection_2}\n\n"
        if goal_prev:
            user_prompt += f"Goals of prior round:\n{goal_prev}\n\n"
            user_prompt += f"Goal Completion Score of prior round:\n{score}\n\n"
        if goal_prev_2:
            user_prompt += f"Goals of two rounds prior:\n{goal_prev_2}\n\n"
            user_prompt += f"Goal Completion Score of two rounds prior:\n{score_2}\n\n"

        # if impressions_str:
        #     user_prompt += f"Impressions: \n{impressions_str}\n"
        user_prompt += "You can keep the previous goal, update the previous goal or create a new one based on your strategy."
        return user_prompt
    
    def goal_update(self, goal: str, goal_embedding: np.ndarray, game: "Game"):
        """
        Maintains the dictionary of goals for the character by round
        """
        round = game.round
        self.goals[round] = {}
        for line in goal.split('\n'):
            if 'Low Priority' in line:
                self.goals[round]['Low Priority'] = line.replace('Low Priority: ', '')
            elif 'Medium Priority' in line:
                self.goals[round]['Medium Priority'] = line.replace('Medium Priority: ', '')
            elif 'High Priority' in line:
                self.goals[round]['High Priority'] = line.replace('High Priority: ', '')
        self.goal_embeddings.update({round: goal_embedding})
        self.update_goals_in_memory(round)

    def get_goals(self, round=-1, priority="all", as_str=False):
        """
        Getter function for goal
            Args:
                round: round number (default is all rounds)
                priority: priority of goal needed (default is all priority goals)

            Returns:
                The goal
        """
        if round != -1 and priority != "all":
            goal = self.goals[round][priority]
        elif round != -1 and priority == "all":
            goal = self.goals[round]
        else:
            goal = self.goals

        if as_str:
            return self.stringify_goal(goal)
        return goal
    
    def stringify_goal(self, goal):
        if isinstance(goal, str):
            return goal
        goal_str = ""
        try:
            if len(goal) > 1:
                goal_str = str(goal)
            else:
                for g in goal.values():
                    goal_str += g + " "
            return goal_str
        except TypeError:
            return goal_str

    def _create_goal_embedding(self, goal: str) -> np.ndarray:
        goal_embedding = get_text_embedding(goal)
        return goal_embedding

    def get_goal_embedding(self, round: int):
        return self.goal_embeddings.get(round, None)
    
    def update_goals_in_memory(self, round):
        curr_embedding = self.get_goal_embedding(round)
        if curr_embedding is not None:
            self.character.memory.set_goal_query(curr_embedding)

    #################evaluation###################
    def evaluate_goals(self, game: "Game"):
        """
        Calls GPT to quantify the goal completion
        User prompt uses: reflection, actions, goals of previous round

        Args:
            game (Game): the game

        Returns:
            str: a completion based score for each priority level
        """
        client = set_up_openai_client("Helicone")

        system_prompt = goal_prompt.evaluate_goals_prompt
        
        user_prompt = self.build_eval_user_prompt

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
        
        scores = response.choices[0].message.content

        self.score_update(scores, game)

        return scores
    
    def build_eval_user_prompt(self, game):

        user_prompt = "Assign the integer by comparing the goal with the reflections provided below:\n"

        goal = self.get_goals(round = game.round)
        user_prompt += f"Goal:{goal}\n" 

        # retrieving apt reflection and action nodes
        reflection_raw = []
        actions_raw = []
        round = game.round
        node_ids = self.character.memory.get_observations_by_round(round)
        for node_id in node_ids:
            node = self.character.memory.get_observation(node_id)
            if node.node_type.value == 3:
                reflection_raw.append(node.node_description)
            if node.node_type.value == 1:
                actions_raw.append(node.node_description)
        reflection = "\n".join(reflection_raw)
        action = "\n".join(actions_raw)

        user_prompt += f"Reflections and Action:\n{reflection}\n\n{action}\n"

        self.recent_reflection = reflection

        return user_prompt
    
    def score_update(self, score: str, game: "Game"):
        """
        Maintains the dictionary of goal completion scores for the character by round
        """
        round = game.round
        self.goal_scores[round] = {}
        for line in score.split('\n'):
            if 'Low Priority' in line:
                try:
                    self.goal_scores[round]['Low Priority'] = int(line.replace('Low Priority: ', ''))
                except ValueError:
                    print("Error: Unable to convert 'Low Priority' to an integer.")
            elif 'Medium Priority' in line:
                try:
                    self.goal_scores[round]['Medium Priority'] = int(line.replace('Medium Priority: ', ''))
                except ValueError:
                    print("Error: Unable to convert 'Medium Priority' to an integer.")
            elif 'High Priority' in line:
                try:
                    self.goal_scores[round]['High Priority'] = int(line.replace('High Priority: ', ''))
                except ValueError:
                    print("Error: Unable to convert 'High Priority' to an integer.")

    def get_goal_scores(self, round=-1, priority="all", as_str=False):
        """
        Getter function for goal completion scores
            Args:
                round: round number (default is all rounds)
                priority: priority of goal score needed (default is all priority goal scores)

            Returns:
                The goal score
        """
        if round != -1 and priority != "all":
            score = self.goal_scores[round][priority]
        elif round != -1 and priority == "all":
            score = self.goal_scores[round]
        else:
            score = self.goal_scores
        return score



