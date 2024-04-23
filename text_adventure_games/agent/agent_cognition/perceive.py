"""
Author: 

File: agent_cognition/perceive.py
Description: defines how agents perceive their environment
"""

from typing import TYPE_CHECKING, Dict

# local imports
from text_adventure_games.agent.memory_stream import MemoryType
from text_adventure_games.utils.general import (parse_location_description, 
                                                find_difference_in_dict_lists)
from text_adventure_games.gpt.gpt_helpers import gpt_get_action_importance

if TYPE_CHECKING:
    from text_adventure_games.games import Game
    from text_adventure_games.things import Character

def collect_perceptions(game: "Game"):
    # Collect the latest information about the location
    return game.describe()
    
def percieve_location(game: "Game", character: "Character"):
    """
    Gather rudimentary information about the current location of the Agent
    and store these observations as new memories (of type MemoryType.ACTION).

    Args:
        game (games.Game): the current game object
    """
    location_description = collect_perceptions(game)
    location_observations = parse_location_description(location_description)

    # check for differences between observations
    diffs_perceived = find_difference_in_dict_lists(character.last_location_observations,
                                                    location_observations)

    # Replace the last perception with the current one
    character.last_location_observations = location_observations.copy()

    add_new_observations(game, character, new_percepts=diffs_perceived)

def add_new_observations(game: "Game", character: "Character", new_percepts: Dict):
    # Create new observations from the differences
    for observations in new_percepts.values():
        print(f"{character.name} sees: {observations}")
        for statement in observations:
            # print(statement)
            command = "Look around at the surroundings"
            action_statement, action_importance, action_keywords = game.parser.summarise_and_score_action(command,
                                                                                                          statement, 
                                                                                                          character)

            character.memory.add_memory(round=game.round,
                                        tick=game.tick,
                                        description=action_statement,
                                        keywords=action_keywords,
                                        location=character.location.name,
                                        success_status=True,
                                        memory_importance=action_importance,
                                        memory_type=MemoryType.PERCEPT.value,
                                        actor_id=character.id)
