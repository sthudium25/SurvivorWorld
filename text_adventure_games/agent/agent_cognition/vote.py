"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent_cognition/vote.py
Description: defines how agents vote for one another. This is specific to Survivor or other similar competitive games.
"""
from collections import Counter
import logging
from random import choice
from typing import List, TYPE_CHECKING
import openai

# local imports
from . import retrieve
from text_adventure_games.assets.prompts import vote_prompt as vp
from text_adventure_games.utils.general import set_up_openai_client
from ..memory_stream import MemoryType

if TYPE_CHECKING:
    from text_adventure_games.things import Character
    from text_adventure_games.games import Game

logger = logging.getLogger(__name__)
VOTING_MAX_OUTPUT = 50

class VotingSession:
    def __init__(self, participants: List["Character"]):
        self.participants = list(set(participants))
        self.tally = Counter()

    def get_vote_options(self, current_voter: "Character", names_only=False):
        """
        Filter out the current voter from the list of participants to generate voting options.

        Args:
            current_voter (Character): the character voting

        Returns:
            list: valid characters to vote for
        """
        if names_only:
            return [p.name for p in self.participants if p != current_voter]
        else:
            return [p for p in self.participants if p != current_voter]

    def run(self, game):
        for voter in self.participants: 
            # print(f"Voter: {voter.name}")
            # 1. Gather context for voter
            # 2. have them cast vote:
            system_prompt, user_prompt = self._gather_voter_context(game, voter)
            try:
                success = False
                while not success:
                    vote = self.gpt_cast_vote(system_prompt, user_prompt)
                    # print(f"Vote received from {voter.name}: {vote}")
                    vote_name, success = self._validate_vote(game, vote, voter)
                    success = success
                    if success:
                        self.tally[vote_name] += 1
                        self._add_vote_to_memory(game, voter, vote_name)
            except (openai.RateLimitError,
                    openai.APIConnectionError,
                    openai.APITimeoutError,
                    openai.APIStatusError) as e:
                # TODO add logging
                logger.error("GPT raised: ", e)

    def _validate_vote(self, game, vote_text, voter):
        vote_kwds = game.parser.extract_keywords(vote_text)
        if "characters" not in vote_kwds:
            return None, False
        elif len(vote_kwds["characters"]) > 0:
            target_name = vote_kwds["characters"][0]
            valid_names = self.get_vote_options(voter, names_only=True)
            if target_name not in valid_names:
                return None, False
            else:
                return target_name, True
            
    def _add_vote_to_memory(self, game: "Game", voter: "Character", vote_target: str) -> None:
        vote_desc = f"During the end of round session, {voter.name} voted for {vote_target} in secret."
        vote_kwds = game.parser.extract_keywords(vote_desc)
        voter.memory.add_memory(game.round,
                                game.tick,
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
        return exiled_participant
    
    def _record_votes(self):
        # TODO: possibly log the votes that each player recieved during the round
        pass

    def _gather_voter_context(self, game: "Game", voter: "Character"):
        world_info = game.world_info
        persona = voter.persona.summary
        goals = voter.goals
        valid_options = self.get_vote_options(voter)
        relationships = voter.impressions.get_multiple_impressions(valid_options)
        query = "".join([
            f"Before the vote, I need to remember what {' '.join(self.get_vote_options(voter, names_only=True))} ",
            "have done to influence my position in the game."
        ])
        hyperrelevant_memories = retrieve.retrieve(game, voter, n=20, query=query)

        system = self._build_system_prompt(world_info, 
                                           persona, 
                                           goals, 
                                           relationships, 
                                           hyperrelevant_memories)
        
        user = self._build_user_prompt(voter=voter)
        return system, user
    
    def _build_system_prompt(self, world, persona, goals, relations, memories):
        system_prompt = ""
        if world:
            system_prompt += f"WORLD INFO: {world}\n\n"
        if persona:
            system_prompt += f"PERSONAL INFO: {persona}\n\n"
        if goals:
            system_prompt += f"YOUR GOALS: {goals}\n\n"
        if relations:
            system_prompt += f"REFLECTIONS ON OTHERS: {relations}\n\n"
        if memories:
            system_prompt += f"SELECT RELEVANT MEMORIES:\n{memories}\n\n"
        system_prompt += vp.vote_system_ending
        return system_prompt
    
    def _build_user_prompt(self, voter):
        user = ""
        choices = self.get_vote_options(voter, names_only=True)
        user += vp.vote_user_prompt.format(vote_options=choices)
        return user
  
    def gpt_cast_vote(self, system_prompt, user_prompt):
        # This method constructs a call to GPT, passing the context as part of a system prompt
        # The user prompt should contain info about recent memories, 
        # the fact that the model must reason about who to vote for,
        # and the list of the valid people to choose to vote for.
        client = set_up_openai_client("Helicone")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            max_tokens=VOTING_MAX_OUTPUT,
            temperature=1,
            top_p=1,
        )

        vote = response.choices[0].message.content
        return vote
    

class JuryVotingSession(VotingSession):
    def __init__(self, jury_members: List["Character"], finalists: List["Character"]):
        super().__init__(participants=jury_members)
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

    def _gather_voter_context(self, game, voter):
        # Adjust to focus on the finalists and the criteria for selecting the winner
        world_info = game.world_info  
        persona = voter.persona.summary  # TODO: adjust with the proper summary when that is finalized
        goals = "Select the deserving winner from the finalists based on the quality of their strategy, gameplay, and contributions."
        relationships = voter.impressions.get_multiple_impressions(self.finalists)
        
        query = "".join([
            f"Before the vote, I need to remember what {' '.join(self.get_vote_options(voter, names_only=True))} ",
            "have done over the course of their game, focusing on their strategy, critical moves made, and strength as a player."
        ])
        hyperrelevant_memories = retrieve.retrieve(game, voter, n=20, query=query)
        
        system = self._build_system_prompt(world_info, persona, goals, relationships, hyperrelevant_memories)  
        user = self._build_user_prompt(voter)  # This might remain similar or be adjusted to reflect the final vote context
        
        return system, user
    
    def determine_winner(self):
        winner_key, _ = self.tally.most_common(1)[0]
        winner = next((f for f in self.finalists if f.name == winner_key), None)
        return winner
