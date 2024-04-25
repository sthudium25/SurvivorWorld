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
from text_adventure_games.assets.prompts import goal_prompt as gp
from text_adventure_games.gpt.gpt_helpers import (GptCallHandler,
                                                  limit_context_length,
                                                  get_prompt_token_count,
                                                  get_token_remainder,
                                                  context_list_to_string)

if TYPE_CHECKING:
    from text_adventure_games.things.characters import Character
    from text_adventure_games.games import Game

GOALS_MAX_OUTPUT = 256

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

        # GPT Call handler attrs
        self.gpt_handler = self._set_up_gpt()
        self.token_offset = 50  # Taking into account a few variable tokens in the user prompt
        self.offset_pad = 5
 
    def _set_up_gpt(self):
        model_params = {
            "api_key_org": "Helicone",
            "model": "gpt-4",
            "max_tokens": GOALS_MAX_OUTPUT,
            "temperature": 1,
            "top_p": 1,
            "max_retries": 5
        }

        return GptCallHandler(**model_params)

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

        system, user = self.build_goal_prompts(game)
        
        goal = self.gpt_handler.generate(system=system, user=user)
        if isinstance(goal, tuple):
            # This occurs when there was a Bad Request Error cause for exceeding token limit
            success, token_difference = goal
            # Add this offset to the calculations of token limits and pad it 
            self.token_offset = token_difference + self.offset_pad
            self.offset_pad += 2 * self.offset_pad 
            return self.gpt_generate_goals(self.game)
        
        # get embedding of goal
        goal_embed = self._create_goal_embedding(goal)
        # for experimentation purposes
        self.goal_update(goal, goal_embed, game)
        return goal
    
    def build_goal_prompts(self, game):
        system_prompt, sys_tkn_count = self.build_system_prompt()
        consumed_tokens = sys_tkn_count + self.token_offset
        user_prompt = self.build_user_prompt(game, consumed_tokens=consumed_tokens)
        return system_prompt, user_prompt
    
    def build_system_prompt(self, game):

        system_prompt = self.character.get_standard_info(game, include_perceptions=False)
        system_prompt += gp.gpt_goals_prompt

        system_tkn_count = get_prompt_token_count(system_prompt, role="system", pad_reply=False, tokenizer=game.parser.tokenizer)
        return system_prompt, system_tkn_count
        
    def build_user_prompt(self, game, consumed_tokens=0):

        always_included = ["Additional context for creating your goal:\n",
                           "You can keep the previous goal, update the previous goal or create a new one based on your strategy."]
        always_included_count = get_prompt_token_count(always_included, 
                                                       role="user", 
                                                       pad_reply=True, 
                                                       tokenizer=game.parser.tokenizer)
        available_tokens = get_token_remainder(self.gpt_handler.model_context_limit,
                                               self.gpt_handler.max_tokens,
                                               consumed_tokens,
                                               always_included_count)
        
        reflections_limit, goals_limit = int(available_tokens * 0.6), int(available_tokens * 0.3)
        # retreive goals and scores for prev round and two rounds prior
        round = game.round
        goal_prev = None
        goal_prev = None
        if round > 0:
            goal_prev = self.get_goals(round=round-1, as_str=True)
            score = self.get_goal_scores(round=round-1, as_str=True)
        if round > 1:
            goal_prev_2 = self.get_goals(round=round-2, as_str=True)
            score_2 = self.get_goal_scores(round=round-2, as_str=True)
        
        # retreive refelction nodes for two rounds prior
        reflection_raw_2 = []
        node_ids = self.character.memory.get_observations_after_round(round-2, inclusive=True)
        for node_id in node_ids:
            node = self.character.memory.get_observation(node_id)
            if node.node_type.value == 3:
                reflection_raw_2.append(node.node_description)
        # reflection_2 = "\n".join(reflection_raw_2)

        # get all character objects
        # char_objects = list(game.characters.values())
        
        # if self.character.use_impressions:
        #     impressions_str = self.character.impressions.get_multiple_impressions(char_objects)
        # else:
        #     impressions_str = None

        user_prompt = always_included[0]
        if reflection_raw_2:
            # user_prompt += f"Reflections on prior round:\n{self.recent_reflection}\n\n"
            user_prompt += "Reflections on last two rounds:"
            context_list = limit_context_length(history=reflection_raw_2,
                                                max_tokens=reflections_limit,
                                                tokenizer=game.parser.tokenizer)
            reflection_2 = context_list_to_string(context_list, sep='\n')
            user_prompt += f"{reflection_2}\n"
        if goal_prev:
            context_list = ["Goals of prior round:", 
                            goal_prev, 
                            "Goal Completion Score of prior round:", 
                            score]
            context_list = limit_context_length(history=context_list,
                                                max_tokens=goals_limit // 2,
                                                tokenizer=game.parser.tokenizer)
            goal_prev_str = context_list_to_string(context_list, sep='\n')
            user_prompt += f"{goal_prev_str}\n\n"
        if goal_prev_2:
            context_list = ["Goals of two rounds prior:", 
                            goal_prev_2, 
                            "Goal Completion Score of two rounds prior:", 
                            score_2]
            context_list = limit_context_length(history=context_list,
                                                max_tokens=goals_limit // 2,
                                                tokenizer=game.parser.tokenizer)
            goal_prev_2_str = context_list_to_string(context_list, sep='\n')
            user_prompt += f"{goal_prev_2_str}\n"

        # if impressions_str:
        #     user_prompt += f"Impressions: \n{impressions_str}\n"
        user_prompt += always_included[1]
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

    # ----------- EVALUATION -----------
    def evaluate_goals(self, game: "Game"):
        """
        Calls GPT to quantify the goal completion
        User prompt uses: reflection, actions, goals of previous round

        Args:
            game (Game): the game

        Returns:
            str: a completion based score for each priority level
        """

        system_prompt = gp.evaluate_goals_prompt
        system_prompt_tokens = get_prompt_token_count(system_prompt, role="system")
        
        user_prompt = self.build_eval_user_prompt(game, consumed_tokens=system_prompt_tokens)
       
        scores = self.gpt_handler.generate(system=system_prompt, user=user_prompt)
        self.score_update(scores, game)

        return scores
    
    def build_eval_user_prompt(self, game, consumed_tokens=0):

        goal = self.get_goals(round=game.round, as_str=True)
        goal_prompt = f"Goal:{goal}\n\n" 

        always_included = ["Score the progress toward the goal that is suggested by the reflections provided below:\n",
                           goal_prompt,
                           "Your reflections and actions from this round:"
                           ]
        always_included_tokens = get_prompt_token_count(always_included, role="user", pad_reply=True)
        available_tokens = get_token_remainder(self.gpt_handler.model_context_limit,
                                               consumed_tokens,
                                               always_included_tokens)

        # retrieving apt reflection and action nodes
        reflections_raw = []
        actions_raw = []
        round = game.round
        node_ids = self.character.memory.get_observations_by_round(round)
        for node_id in node_ids:
            node = self.character.memory.get_observation(node_id)
            # Get the reflections and actions that this agent has made this round
            if node.node_type.value == 3 and node.node_is_self == 1:
                reflections_raw.append(node.node_description)
            if node.node_type.value == 1 and node.node_is_self == 1:
                actions_raw.append(node.node_description)

        reflections_list = limit_context_length(history=reflections_raw,
                                                max_tokens=available_tokens // 2,
                                                tokenizer=game.parser.tokenizer)
        reflections_str = context_list_to_string(reflections_list, sep='\n')
        
        actions_list = limit_context_length(history=actions_raw,
                                            max_tokens=available_tokens // 2,
                                            tokenizer=game.parser.tokenizer)
        actions_str = context_list_to_string(actions_list, sep='\n')
        user_prompt = always_included[0]
        user_prompt += goal_prompt
        user_prompt += f"Reflections:\n{reflections_str}\n\n"
        user_prompt += f"Actions: {actions_str}\n"
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

        if as_str:
            return self.stringify_goal(score)
        return score
