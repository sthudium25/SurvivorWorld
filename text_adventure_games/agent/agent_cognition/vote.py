"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent_cognition/vote.py
Description: defines how agents vote for one another. This is specific to Survivor or other similar competitive games.
"""
from collections import Counter, defaultdict
import json
import logging
from random import choice
from typing import List, TYPE_CHECKING, Union
import openai

# local imports
from . import retrieve
from text_adventure_games.assets.prompts import vote_prompt as vp
from text_adventure_games.utils.general import get_logger_extras
from text_adventure_games.gpt.gpt_helpers import (limit_context_length,
                                                  get_prompt_token_count,
                                                  get_token_remainder,
                                                  context_list_to_string,
                                                  GptCallHandler)
from ..memory_stream import MemoryType

if TYPE_CHECKING:
    from text_adventure_games.things import Character
    from text_adventure_games.games import Game

VOTING_MAX_OUTPUT = 100

class VotingSession:
    def __init__(self, game: "Game", participants: List["Character"]):
        self.game = game
        self.participants = self._set_participants(participants)
        self.tally = Counter()
        self.voter_record = defaultdict(str)

        # gpt call attrs
        self.gpt_handler = self._set_up_gpt()
        self.token_offset = 0
        self.offset_pad = 5

    def _set_participants(self, participants):
        immune = []
        for p in participants:
            if p.get_property("immune"):
                # This character possesses a hidden immunity idol
                immune.append(p)
        if len(immune) > 0:
            print(f"{immune[0].name} is safe from the vote")
            self._add_idol_possession_to_memory(immune, participants)
        self.immune = immune
        return list(set(participants))

    def _add_idol_possession_to_memory(self, immune_players, participants):
        immune_desc = vp.immunity_memory_prompt.format(immune_players=", ".join([ip.name for ip in immune_players]))
        immunity_kwds = self.game.parser.extract_keywords(immune_desc)
        for p in participants:
            p.memory.add_memory(self.game.round,
                                self.game.tick,
                                immune_desc,
                                keywords=immunity_kwds,
                                location=None,
                                success_status=True,
                                memory_importance=10,
                                memory_type=MemoryType.ACTION.value,
                                actor_id=p.id)

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

    def get_vote_options(self, current_voter: "Character", names_only=False):
        """
        Filter out the current voter from the list of participants to generate voting options.

        Args:
            current_voter (Character): the character voting

        Returns:
            list: valid characters to vote for
        """
        predicate = lambda p: (p != current_voter) and (p not in self.immune)
        if names_only:
            return [p.name for p in self.participants if predicate]
        else:
            return [p for p in self.participants if predicate]

    def run(self):
        for voter in self.participants: 
            # print(f"Voter: {voter.name}")
            # 1. Gather context for voter
            # 2. have them cast vote:
            system_prompt, user_prompt = self._gather_voter_context(voter)

            success = False
            for i in range(5):
                vote = self.gpt_cast_vote(system_prompt, user_prompt)
                vote_name, vote_confessional, success = self._validate_vote(vote, voter)
                success = success
                if success:
                    self._record_vote(voter, vote_name, vote_confessional)
                    break
                elif i == 4:
                    # This vote has failed too many times so get a random vote
                    print(f"{voter.name} is failed to vote properly. Making a random choice.")
                    valid_options = self.get_vote_options(voter, names_only=True)
                    random_vote = choice(valid_options)
                    self._record_vote(voter, random_vote, "This was a randomized vote because GPT failed to vote properly.")
                    break
        
        # Clean up / reset any idols used in this round
        self._cleanup()

    def _record_vote(self, voter, vote_name, vote_confessional):
        self.tally[vote_name] += 1
        self._add_vote_to_memory(voter, vote_name)
        self.voter_record[voter.name] = vote_name
        self._log_confessional(voter, vote_confessional)

    def _validate_vote(self, vote_text, voter):
        try:
            vote_dict = json.loads(vote_text)
            vote_target = vote_dict["target"]
            vote_reason = vote_dict["reason"]
        except (json.JSONDecodeError,
                KeyError):
            return None, None, False
        else:
            vote_kwds = self.game.parser.extract_keywords(vote_target)
            if "characters" not in vote_kwds:
                return None, None, False
            elif len(vote_kwds["characters"]) > 0:
                target_name = vote_kwds["characters"][0]
                valid_names = self.get_vote_options(voter, names_only=True)
                if target_name not in valid_names:
                    return None, None, False
                else:
                    return target_name, vote_reason, True
            
    def _add_vote_to_memory(self, voter: "Character", vote_target: str) -> None:
        vote_desc = f"During the end of round session, {voter.name} voted for {vote_target} in secret."
        print(vote_desc)
        vote_kwds = self.game.parser.extract_keywords(vote_desc)
        voter.memory.add_memory(self.game.round,
                                self.game.tick,
                                vote_desc,
                                keywords=vote_kwds,
                                location=None,
                                success_status=True,
                                memory_importance=10,
                                memory_type=MemoryType.ACTION.value,
                                actor_id=voter.id)

    def read_votes(self):
        """
        Count the cast votes and return the character with the highest tally.
        In the case of a tie, a random choice is made.

        Returns:
            exiled: Character
        """
        top_count = None
        try:
            top_count = self.tally.most_common(1)[0][1]
        except (KeyError, IndexError):
            exiled_key, _ = self.tally.most_common(1)[0]
        if top_count:
            choices = [(c, v) for c, v in self.tally.items() if v == top_count]
            exiled_key = choice(choices)[0]
         
        exiled_participant = next((p for p in self.participants if p.name == exiled_key), None)
        self.exiled = [exiled_participant.name]
        return exiled_participant
    
    def record_vote(self, voter):
        record = [{"votes_received": self.tally.get(voter.name, 0)}, 
                  {"target": self.voter_record.get(voter.name, "None")},
                  {"is_safe": voter.name not in self.exiled}]
        return record

    def _gather_voter_context(self, voter: "Character"):
        voter_std_info = voter.get_standard_info(self.game, include_perceptions=False)
        valid_options = self.get_vote_options(voter)
        try:
            impressions = voter.impressions.get_multiple_impressions(valid_options)
        except AttributeError:
            impressions = None
        query = "".join([
            f"Before the vote, I need to remember what {' '.join(self.get_vote_options(voter, names_only=True))} ",
            "have done to influence my position in the game."
        ])
        hyperrelevant_memories = retrieve.retrieve(self.game, voter, n=50, query=query)

        system = self._build_system_prompt(voter_std_info,
                                           prompt_ending=vp.vote_system_ending)
        
        system_token_count = get_prompt_token_count(content=system,
                                                    role="system",
                                                    tokenizer=self.game.parser.tokenizer)
        tokens_consumed = system_token_count + self.token_offset
        
        user = self._build_user_prompt(voter=voter,
                                       impressions=impressions, 
                                       memories=hyperrelevant_memories,
                                       prompt_ending=vp.vote_user_prompt,
                                       consumed_tokens=tokens_consumed)
        return system, user
    
    def _build_system_prompt(self, standard_info, prompt_ending):
        system_prompt = ""
        if standard_info:
            system_prompt += standard_info
        system_prompt += prompt_ending
        return system_prompt
    
    def _build_user_prompt(self, 
                           voter, 
                           impressions: list,
                           memories: list,
                           prompt_ending: str,
                           consumed_tokens: int = 0):
        
        choices = self.get_vote_options(voter, names_only=True)
        user_prompt_end = prompt_ending.format(vote_options=choices)

        always_included_count = get_prompt_token_count(content=user_prompt_end,
                                                       role="user",
                                                       pad_reply=True)
        
        user_available_tokens = get_token_remainder(self.gpt_handler.model_context_limit, 
                                                    self.gpt_handler.max_tokens,
                                                    consumed_tokens,
                                                    always_included_count)
        
        # Initially allot half of the remaining tokens to the impressions
        context_limit = user_available_tokens // 2

        user_prompt = ""
        if impressions:
            impressions, imp_token_count = limit_context_length(impressions,
                                                                context_limit,
                                                                return_count=True)
            
            user_prompt += f"Your REFLECTIONS on other:\n{context_list_to_string(impressions)}\n\n"
            context_limit = get_token_remainder(user_available_tokens,
                                                imp_token_count)
        if memories:
            memories = limit_context_length(memories,
                                            context_limit)
                                                                
            user_prompt += f"SELECT RELEVANT MEMORIES to the vote:\n{context_list_to_string(memories)}\n\n"

        user_prompt += user_prompt_end
        return user_prompt
  
    def gpt_cast_vote(self, system_prompt, user_prompt):
        # This method constructs a call to GPT, passing the context as part of a system prompt
        # The user prompt should contain info about recent memories, 
        # the fact that the model must reason about who to vote for,
        # and the list of the valid people to choose to vote for.
        
        vote = self.gpt_handler.generate(system_prompt, user_prompt)
        if isinstance(vote, tuple):
            # This occurs when there was a Bad Request Error cause for exceeding token limit
            success, token_difference = vote
            # Add this offset to the calculations of token limits and pad it 
            self.token_offset = token_difference + self.offset_pad
            self.offset_pad += 2 * self.offset_pad 
            return self.run(self.game)
        return vote

    def _log_confessional(self, voter: "Character", message: str):
        extras = get_logger_extras(self.game, voter)
        extras["type"] = "Confessional"
        message = f"Target: {self.voter_record.get(voter.name, 'None')}; {message}" 
        self.game.logger.debug(msg=message, extra=extras)

    def log_vote(self, exiled: "Character", message: str):
        extras = get_logger_extras(self.game, exiled)
        extras["type"] = "Vote"
        self.game.logger.debug(msg=message, extra=extras)

    def _cleanup(self):
        if not self.immune:
            return True
        for character in self.immune:
            idol = character.get_item_by_name("idol")
            if idol:
                character.remove_from_inventory(idol)
            character.set_property("immune", False)
        return True

class JuryVotingSession(VotingSession):
    def __init__(self, game: "Game", jury_members: List["Character"], finalists: List["Character"]):
        super().__init__(game=game, participants=jury_members)
        self.finalists = finalists

    def get_vote_options(self, current_voter: "Character", names_only=False):
        """
        Override the parent class version. 
        Only need the finalists list, which is already separate from jury members

        Args:
            current_voter (Character): the jury member voting (only present for compatibility)
            names_only (bool, optional): return agent names only or full Character objects. Defaults to False.

        Returns:
            _type_: _description_
        """
        if names_only:
            return [f.name for f in self.finalists]
        else:
            return self.finalists

    def _gather_voter_context(self, voter):
        # Adjust to focus on the finalists and the criteria for selecting the winner
        voter_std_info = voter.get_standard_info(self.game, include_goals=False, include_perceptions=False)
        try:
            impressions = voter.impressions.get_multiple_impressions(self.finalists)
        except AttributeError:
            impressions = None
        
        query = "".join([
            f"Before the final vote, I need to remember what {' '.join(self.get_vote_options(voter, names_only=True))} ",
            "have done over the course of their game, focusing on their strategy, critical moves made, and strength as a player."
        ])
        hyperrelevant_memories = retrieve.retrieve(self.game, voter, n=50, query=query)
        
        system = self._build_system_prompt(voter_std_info,
                                           prompt_ending=vp.jury_system_ending)
        
        system_token_count = get_prompt_token_count(content=system,
                                                    role="system",
                                                    tokenizer=self.game.parser.tokenizer)
        tokens_consumed = system_token_count + self.token_offset
        
        user = self._build_user_prompt(voter=voter,
                                       impressions=impressions, 
                                       memories=hyperrelevant_memories,
                                       prompt_ending=vp.jury_user_prompt,
                                       consumed_tokens=tokens_consumed)
        
        return system, user
    
    def determine_winner(self):
        winner_key, _ = self.tally.most_common(1)[0]
        winner = next((f for f in self.finalists if f.name == winner_key), None)
        exiled = []
        for f in self.finalists:
            if f.name != winner.name:
                exiled.append(f.name)
        self.exiled = exiled
        return winner
