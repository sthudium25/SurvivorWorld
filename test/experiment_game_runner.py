import random
import os
from itertools import cycle
from text_adventure_games import games, things
from text_adventure_games.agent.persona import Persona
from text_adventure_games.things.characters import GenerativeAgent
from text_adventure_games.utils.consts import get_assets_path
from text_adventure_games.utils.build_agent import build_agent


GROUP_MAPPING = {"A": (False, False),
                 "B": (True, False),
                 "C": (False, True),
                 "D": (True, True)}


class ClassicGame(games.SurvivorGame):
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


class ExplorationGame(games.SurvivorGame):
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
                         experiment_id=experiment_id,
                         end_state_check="on_action")
        
    def is_won(self):
        """
        Override the default behavior of SurvivorGame is_won to specify the 
        end state for the exploration game.

        Returns:
            bool: has the game been won
        """
        # EXPLORATION GAME
        for character in list(self.characters.values()):
            if character.get_property("immune"):
                print("{name} found the idol! Game is over".format(name=character.name))
                return True
        return False
            
def build_exploration(experiment_name: str = "exp1",
                      experiment_id: int = 1, 
                      max_ticks: int = 6, 
                      num_finalists: int = 2,
                      architecture: str = "A", 
                      personas_path: str = ".",
                      random_placement: bool = False) -> games.Game:
  
    locations = build_game_locations()

    # Additional items
    machete4 = things.Item(
        "machete2",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    locations.get("ocean").add_item(machete4)
    # ocean.add_item(machete4)

    machete5 = things.Item(
        "machete3",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    locations.get("jungle_path").add_item(machete5)

    # EXPLORATION
    clue = things.Item(
        "idol clue",
        "a clue to the idol",
        "A CLUE THAT SAYS THE IDOL CAN BE FOUND IN THE JUNGLE WITH A MACHETE",
    )
    locations.get("cliffs").add_item(clue)

    # Characters
    characters = []
    # EXPLORATION
    start_at = locations.get("camp")

    character_jsons = collect_game_characters(personas_path)
    for f in character_jsons:
        persona = Persona.import_persona(f)
        character = GenerativeAgent(persona, architecture)
        location = locations.get("camp")
        location.add_character(character)
        characters.append(character)
        print(f"Character {character.name} starts at {location.name} and belongs to Group {architecture}")
    
    player = characters.pop(0)

    # The Game
    game = ExplorationGame(start_at, 
                           player, 
                           characters, 
                           custom_actions=None,
                           max_ticks=max_ticks,
                           num_finalists=num_finalists,
                           experiment_name=experiment_name,
                           experiment_id=experiment_id)

    return game

def build_classic(experiment_name: str = "exp1",
                  experiment_id: int = 1,
                  num_characters: int = 4,
                  max_ticks: int = 6, 
                  num_finalists: int = 2, 
                  personas_path: str = ".",
                  random_placement: bool = False) -> games.Game:

    # Valid start locations:
    locs = build_game_locations()
    # Characters
    characters = []

    if random_placement:
        location_cycler = cycle(list(locs.values()))
        location_assignments = [next(location_cycler) for _ in range(num_characters)]
    else:
        location_assignments = [locs.get("camp")] * num_characters
    group_cycler = cycle(GROUP_MAPPING.keys())
    group_assignments = [next(group_cycler) for _ in range(num_characters)]
    random.shuffle(group_assignments)
    random.shuffle(location_assignments)
    start_at = location_assignments[0]

    character_jsons = collect_game_characters(personas_path)
    if len(character_jsons) < num_characters:
        diff = num_characters - len(character_jsons)
        character_jsons.extend([None] * diff)

    for i, filename in enumerate(character_jsons):
        if not filename:
            persona = build_agent("An quirky contestant that is must see TV on a reality show.", facts_new=True)
        else:
            persona = Persona.import_persona(filename)
        character = GenerativeAgent(persona, group_assignments[i])
        location = location_assignments[i]
        location.add_character(character)
        characters.append(character)
        print(f"Character {character.name} starts at {location.name} and belongs to Group {group_assignments[i]}")
    
    player = characters.pop(0)

    # The Game
    game = ClassicGame(start_at, 
                       player, 
                       characters, 
                       custom_actions=None,
                       max_ticks=max_ticks,
                       num_finalists=num_finalists,
                       experiment_name=experiment_name,
                       experiment_id=experiment_id)

    return game

def collect_game_characters(personas_path):
    if not os.path.isdir(personas_path):
        package_assets = get_assets_path()
        personas_path = os.path.join(package_assets, personas_path)
    character_files = []
    if os.path.exists(personas_path):
        for filename in os.listdir(personas_path):
            if filename.endswith(".json"):
                print("Adding character file: ", filename)
                character_path = os.path.join(personas_path, filename)
                character_files.append(character_path)

    return character_files

def build_game_locations():
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

    # No starting in the jungle!
    return {"camp": camp, "cliffs": cliffs, "beach": beach, "ocean": ocean, "jungle_path": jungle_path, "well": well}
