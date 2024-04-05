"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent_cognition/vote.py
Description: defines how agents vote for one another. This is specific to Survivor or other similar competitive games.
"""
from collections import Counter
import logging
from typing import List, TYPE_CHECKING
import openai

from text_adventure_games.utils.general import set_up_openai_client

# local imports
from . import retrieve
from text_adventure_games.assets.prompts import vote_prompt as vp
if TYPE_CHECKING:
    from text_adventure_games.things import Character

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
            # 1. Gather context for voter
            # 2. have them cast vote:
            system_prompt, user_prompt = self._gather_voter_context(game, voter)
            try:
                success = False
                while not success:
                    vote = self.gpt_cast_vote(system_prompt, user_prompt)
                    vote_name, success = self._validate_vote(game, vote, voter)
                    success = success
                    if success:
                        self.tally[vote_name] += 1
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

    def read_votes(self):
        exiled_key, _ = self.tally.most_common(1)[0]
        exiled_participant = next((p for p in self.participants if f"{p.name}_{p.id}" == exiled_key), None)
        return exiled_participant
    
    def _record_votes(self):
        # TODO: possibly log the votes that each player reecieved during the round
        pass

    def _gather_voter_context(self, game, voter):
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
        
        user = self._build_system_prompt()
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
