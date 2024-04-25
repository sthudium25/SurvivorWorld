import logging
import os
import random
from SurvivorWorld.text_adventure_games import games, things, actions, blocks
from SurvivorWorld.text_adventure_games.agent.persona import Persona
from SurvivorWorld.text_adventure_games.things.characters import GenerativeAgent
from SurvivorWorld.text_adventure_games.utils.build_agent import build_agent
from SurvivorWorld.text_adventure_games.utils.custom_logging import logging_setup
from SurvivorWorld.text_adventure_games.utils.custom_logging import logger

GROUP_MAPPING = {"A": (False, False),
                 "B": (True, False),
                 "C": (False, True),
                 "D": (True, True)}


class ExperimentGame(games.SurvivorGame):
    def __init__(
            self,
            start_at: things.Location,
            player: things.Character,
            characters=None,
            custom_actions=None,
            max_ticks=5,
            num_finalists=2,
            experiment_name="exp1",
            experiment_id=1
        ):
            super().__init__(start_at,
                            player, 
                            characters, 
                            custom_actions, 
                            max_ticks=max_ticks, 
                            num_finalists=num_finalists,
                            experiment_name=experiment_name,
                            experiment_id=experiment_id)
            
def build_experiment(experiment_name, experiment_id, max_ticks=2, num_finalists=2) -> games.Game:
      # Locations
    camp = things.Location(
        "Camp",
        "the tribe's base camp."
    )
    cliffs = things.Location(
        "Cliffs",
        """the front of some steep cliffs.
            Climb them carefully so you don't fall.""",
    )
    beach = things.Location(
        "Beach",
        "the beach, toes in the sand. In front of you is the vast ocean."
    )
    ocean = things.Location(
        "Ocean",
        "the edge of the ocean with waves washing up around your knees.",
    )
    jungle_path = things.Location(
        "Jungle Path",
        "a jungle path towards the well.",
    )
    well = things.Location(
        "Well",
        "the water well where you can get water for your tribe.",
    )
    jungle = things.Location(
        "Jungle",
        "the deep jungle. There could be treasures lurking nearby.",
    )

    camp.add_connection("out", beach)
    beach.add_connection("north", jungle_path)
    beach.add_connection("south", ocean)
    beach.add_connection("west", cliffs)
    beach.add_connection("in", camp)
    jungle_path.add_connection("south", beach)
    jungle_path.add_connection("east", well)
    jungle_path.add_connection("north", jungle)
    well.add_connection("west", jungle_path)
    jungle.add_connection("south", jungle_path)
    ocean.add_connection("north", beach)
    cliffs.add_connection("east", beach)

    # Gettable Items
    fishing_pole = things.Item(
        "pole",
        "a fishing pole",
        "A SIMPLE FISHING POLE.",
    )
    ocean.add_item(fishing_pole)

    machete = things.Item(
        "machete",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    camp.add_item(machete)

    # Characters
    characters = []
    char_locations = [camp, camp, beach, beach, jungle_path, jungle_path, ocean, ocean]
    char_groups = ["A", "A", "B", "B", "C", "C", "D", "D"]
    random.shuffle(char_groups)
    random.shuffle(char_locations)
    start_at = char_locations[0]

    for i, filename in enumerate(os.listdir("game_personas")):
        if filename.endswith(".json"):
            persona = Persona.import_persona("game_personas/" + filename)
            character = GenerativeAgent(persona, char_groups[i])
            location = char_locations[i]
            location.add_character(character)
            characters.append(character)
            print(f"Character {character.name} starts at {location.name} and belongs to Group {char_groups[i]}")
    
    player = characters.pop(0)

    # The Game
    game = ExperimentGame(start_at, 
                            player, 
                            characters, 
                            custom_actions=None,
                            max_ticks=max_ticks,
                            num_finalists=num_finalists,
                            experiment_name=experiment_name,
                            experiment_id=experiment_id)

    return game
