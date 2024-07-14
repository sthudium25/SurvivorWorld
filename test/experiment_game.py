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
            
def build_experiment(experiment_name, experiment_id, max_ticks=6, num_finalists=2, architecture="A") -> games.Game:
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
        "the deep jungle. There could be treasures hiding nearby.",
    )
    jungle.set_property("has_idol", True)

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
    ocean.set_property("has_fish", True)

    machete1 = things.Item(
        "machete1",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    camp.add_item(machete1)

    machete2 = things.Item(
        "machete2",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    well.add_item(machete2)

    machete3 = things.Item(
        "machete3",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    beach.add_item(machete3)

    machete4 = things.Item(
        "machete2",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    ocean.add_item(machete4)

    machete5 = things.Item(
        "machete3",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    jungle_path.add_item(machete5)


    #EXPLORATION
    clue = things.Item(
        "idol clue",
        "a clue to the idol",
        "A CLUE THAT SAYS THE IDOL CAN BE FOUND IN THE JUNGLE WITH A MACHETE",
    )
    cliffs.add_item(clue)

    # Characters
    characters = []
    # EXPLORATION
    start_at = camp

    for i, filename in enumerate(os.listdir("exploration_personas")):
        if filename.endswith(".json"):
            persona = Persona.import_persona("exploration_personas/" + filename)
            character = GenerativeAgent(persona, architecture)
            location = camp
            location.add_character(character)
            characters.append(character)
            print(f"Character {character.name} starts at {location.name} and belongs to Group {architecture}")
    
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
