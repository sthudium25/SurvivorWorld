import random
import os
from itertools import cycle
from typing import List
from text_adventure_games import games, things
from text_adventure_games.agent.persona import Persona
from text_adventure_games.assets.prompts import world_info_prompt
from text_adventure_games.things.characters import GenerativeAgent, DiscoveryAgent
from text_adventure_games.utils.consts import get_assets_path
from text_adventure_games.utils.build_agent import build_agent
from text_adventure_games.utils.general import get_logger_extras


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
    
class DiscoveryGame(games.SurvivorGame):
    def __init__(
            self,
            start_at: things.Location,
            player: things.Character,
            characters=None,
            custom_actions=None,
            max_ticks=5,
            num_finalists=2,
            max_rounds=10,
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
        
        self.remaining_idols = self._get_idols_count()
        self.max_rounds = max_rounds

    def is_won(self):
        """
        Override the default behavior of SurvivorGame is_won to specify the 
        end state for the discovery game.

        Returns:
            bool: has the game been won
        """
        # EXPLORATION GAME
        remaining_idols = self._get_idols_count()
        if remaining_idols == 0:
            print("All idols have been found! Game is over")
            self._log_player_scores()
            return True
        if self.round > self.max_rounds - 1:
            print("The time-limit of the game has been reached.")
            self._log_player_scores()
            return True
        self.remaining_idols = remaining_idols
        return False
    
    def _get_idols_count(self):
        remaining_idols = 0
        for location in list(self.locations.values()):
            if location.get_property("has_idol"):
                remaining_idols += 1
        return remaining_idols
    
    def _log_player_scores(self):
        for agent in list(self.characters.values()):
            message = f"{agent.name}'s final score: {agent.score:.2f}"
            extras = get_logger_extras(self, agent)
            extras["type"] = "Scores"
            self.logger.debug(msg=message, extra=extras)
    
    def _get_player_alliance(self, ids_only=False, names_only=False, as_str=False):
        if ids_only:
            return [ally.id for ally in self.player.get_teammates()]
        if names_only:
            return [ally for ally in self.player.get_teammates(names_only=names_only, as_str=as_str)]
        return self.player.get_teammates()
        
    def update_world_info(self):
        params = {"idol_value": 100 - self.total_ticks,
                  "contestant_names_locs": ", ".join([f"{c.name} who is at {c.location.name}" 
                                                      for c in self.characters.values() 
                                                      if (c.id != self.player.id) and (c.id not in self._get_player_alliance(ids_only=True))]),
                  "partner_count": len(self._get_player_alliance()),
                  "teammates": self._get_player_alliance(names_only=True, as_str=True),
                  "game_locations": ", ".join(list(self.locations.keys())),
                  "remaining_idols": self.remaining_idols,
                  "rounds_remaining": 11 - self.round,
                  "turns_left_this_round": self.max_ticks_per_round - (self.tick - 1),
                  "n": self.round}
        self.world_info = world_info_prompt.discovery_world_info.format(**params)

    def get_basic_game_goal(self):
        params = {"teammates": self._get_player_alliance(names_only=True, as_str=True)} 
        return world_info_prompt.discovery_basic_goal.format(**params)
            
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

def build_discovery(experiment_name: str = "exp1",
                    experiment_id: int = 1,
                    num_characters: int = 6,
                    max_ticks: int = 6, 
                    num_finalists: int = 2,
                    max_rounds: int = 10,
                    personas_path: str = ".",
                    random_placement: bool = False) -> games.Game:
    
    # locations
    locations = build_game_locations()
    locations = build_discovery_locations(locations)
    
    # Characters
    characters = []
    start_at = locations.get("camp")

    group_cycler = cycle(["A", "E", "D"]) if num_characters == 6 else cycle(["A", "B", "C", "D"])
    # group_assignments = [next(group_cycler) for _ in range(num_characters)]

    character_jsons = collect_game_characters(personas_path, partition=["Detective", "Explorer"])
    detective_files = character_jsons.get("Detective", [])
    explorer_files = character_jsons.get("Explorer", [])

    # Ensure both lists have the same length by truncating the longer list
    # Randomize the ordering of the persona files so it has no effect across experiments
    min_length = min(len(detective_files), len(explorer_files))
    detective_files = detective_files[:min_length]
    explorer_files = explorer_files[:min_length]
    random.shuffle(detective_files)
    random.shuffle(explorer_files)

    for teams in zip(detective_files, explorer_files):
        # print("Current team files: ", teams)
        architecture = next(group_cycler)
        # print(f"Creating team {architecture}")
        team = []
        for f in teams:
            # print(f"Fiile to character; {f}")
            persona = Persona.import_persona(f)
            character = DiscoveryAgent(persona, 
                                       group=architecture)
            team.append(character)
            location = locations.get("camp")
            location.add_character(character)
            characters.append(character)
            print(f"Character {character.name} starts at {location.name} and belongs to Group {architecture}")
        for character in team:
            character.set_teammates(members=team)

    player = characters.pop(0)

    # The Game
    game = DiscoveryGame(start_at, 
                         player, 
                         characters, 
                         custom_actions=None,
                         max_ticks=max_ticks,
                         num_finalists=num_finalists,
                         max_rounds=max_rounds,
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

def collect_game_characters(personas_path, partition: List[str] = None):
    if not os.path.isdir(personas_path):
        package_assets = get_assets_path()
        personas_path = os.path.join(package_assets, personas_path)
    if partition:
        character_files = {key: [] for key in partition}
    else: 
        character_files = []
    if os.path.exists(personas_path):
        for filename in os.listdir(personas_path):
            if filename.endswith(".json"):
                print("Adding character file: ", filename)
                character_path = os.path.join(personas_path, filename)
                if partition:
                    for key in partition:
                        if key in filename:
                            character_files[key].append(character_path)
                            break
                else:
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
    jungle.set_property("tool_required", True)
    jungle.set_property("idol_found", False)
    jungle_fail_message = "but the vines get in the way and it becomes impossible without the right tool (a machete!)."
    jungle.set_property("search_fail", jungle_fail_message)
    jungle.set_property("found_message", "This idol has already been found by another team! Hurry to find one of the remaining idols!")

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

def build_discovery_locations(base_locations):

    # Additional locations/connections
    base_locations.get("camp").add_connection("north", base_locations.get("well"))

    waterfall = things.Location(
        "Waterfall",
        "A stunning waterfall creates a veil of mist.",
    )
    waterfall.set_property("has_idol", True)
    waterfall.set_property("tool_required", True)
    waterfall.set_property("idol_found", False)
    waterfall.set_property("found_message", "This idol has already been found by another team! Hurry to find one of the remaining idols!")
    waterfall_fail_message = "but the rocks are too slippery and it becomes impossible without the right tool (a sturdy stick!)."
    waterfall.set_property("search_fail", waterfall_fail_message)
    waterfall.add_connection("west", base_locations.get("well"))
    base_locations.get("well").add_connection("east", waterfall)

    rocky_shores = things.Location(
        "rocky shore",
        "Slippery tidepools with rocks beaten by waves."
    )
    rocky_shores.set_property("has_idol", True)
    rocky_shores.set_property("tool_required", False)
    rocky_shores.set_property("idol_found", False)
    rocky_shores.set_property("found_message", "This idol has already been found by another team! Hurry to find one of the remaining idols!")
    rocky_shores.set_property("search_fail", "but the tide is too high and dangerous to wade across the rocks. It will subside next round and you should try again then! ")
    rocky_shores.add_connection("north", base_locations.get("camp"))
    base_locations.get("camp").add_connection("south", rocky_shores)

    lazy_river = things.Location(
        "lazy river",
        "the banks of a murky, winding river"
    )
    lazy_river.add_connection("south", base_locations.get("well"))
    base_locations.get("well").add_connection("north", lazy_river)

    # Additional items
    stick1 = things.Item(
        "stick",
        "a long stick",
        "A sturdy stick to keep balanced on slippery rocks."
    )
    base_locations.get("well").add_item(stick1)

    stick2 = things.Item(
        "stick",
        "a long stick",
        "A sturdy stick to keep balanced on slippery rocks."
    )
    base_locations.get("beach").add_item(stick2)

    stick3 = things.Item(
        "stick",
        "a long stick",
        "A sturdy stick to keep balanced on slippery rocks."
    )
    base_locations.get("ocean").add_item(stick3)

    stick4 = things.Item(
        "stick",
        "a long stick",
        "A sturdy stick to keep balanced on slippery rocks."
    )
    base_locations.get("jungle_path").add_item(stick4)

    machete4 = things.Item(
        "machete2",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    base_locations.get("ocean").add_item(machete4)
    # ocean.add_item(machete4)

    machete5 = things.Item(
        "machete3",
        "a sharp machete",
        "A SHARP MACHETE USED FOR CUTTING VINES.",
    )
    base_locations.get("jungle_path").add_item(machete5)

    # EXPLORATION
    clue1 = things.Item(
        "idol clue",
        "a clue to the idol",
        "A CLUE THAT SAYS THE IDOL CAN BE FOUND IN THE JUNGLE WITH A MACHETE",
    )
    base_locations.get("cliffs").add_item(clue1)
    clue1_message = "".join([
        "'An idol can be found by searching the jungle with a machete.' ",
        "'You can fail this action but keep trying as long as you have a machete and are in the jungle!' ",
        "'If you pick up and hold this clue while searching, you'll have a better chance of discovering the idol!'"
    ])
    clue1.set_property("clue_content", clue1_message)

    clue2 = things.Item(
        "idol clue",
        "a clue to the idol",
        "A CLUE THAT SAYS THE IDOL CAN BE FOUND IN THE WATERFALL WITH A STICK",
    )
    base_locations.get("well").add_item(clue2)
    clue2_message = "".join([
        "'An idol can be found by searching the waterfall with a sturdy stick.' ",
        "'You can fail this action but keep trying as long as you have a stick and are at the waterfall!' ",
        "'If you pick up and hold this clue while searching, you'll have a better chance of discovering the idol!'"
    ])
    clue2.set_property("clue_content", clue2_message)

    clue3 = things.Item(
        "idol clue",
        "a clue to the idol",
        "A CLUE THAT SAYS THE IDOL CAN BE FOUND IN THE JUNGLE WITH A MACHETE",
    )
    base_locations.get("ocean").add_item(clue3)
    clue3_message = "".join([
        "'An idol can be found by searching the jungle with a machete.' ",
        "'You can fail this action but keep trying as long as you have a machete and are in the jungle!' ",
        "'If you pick up and hold this clue while searching, you'll have a better chance of discovering the idol!'"
    ])
    clue3.set_property("clue_content", clue3_message)

    clue4 = things.Item(
        "idol clue",
        "a clue to the idol",
        "A CLUE THAT SAYS THE IDOL CAN BE FOUND ON THE ROCKY SHORES DURING CERTAIN ROUNDS",
    )
    lazy_river.add_item(clue4)
    clue4_message = "".join([
        "'An idol can be found by searching rocky shores, but be careful of the tide!' ",
        "'The tide behaves in a cyclic manner, so you must plan your search for the correct timing. ' ",
        "'If you pick up and hold this clue while searching, you'll have a better chance of discovering the idol!'"
    ])
    clue4.set_property("clue_content", clue4_message)
    
    base_locations["waterfall"] = waterfall
    base_locations["rocky_shore"] = rocky_shores
    base_locations["lazy_river"] = lazy_river

    return base_locations

def build_mini_discovery(experiment_name: str = "exp1",
                         experiment_id: int = 1,
                         max_ticks: int = 6, 
                         num_finalists: int = 2,
                         personas_path: str = ".",
                         random_placement: bool = False) -> games.Game:
    
    cliffs = things.Location(
        "Cliffs",
        """the front of some steep cliffs.
            Climb them carefully so you don't fall.""",
    )
     
    clue = things.Item(
        "idol clue",
        "a clue to the idol",
        "A CLUE THAT SAYS THE IDOL CAN BE FOUND IN THE JUNGLE WITH A MACHETE",
    )
    cliffs.add_item(clue)
    clue1_message = "".join([
        "'An idol can be found by searching the jungle with a machete.' ",
        "'You can fail this action but keep trying as long as you have a machete and are in the jungle!' ",
        "'If you pick up and hold this clue while searching, you'll have a better chance of discovering the idol!'"
    ])
    clue.set_property("clue_content", clue1_message)
    cliffs.set_property("has_idol", True)
    cliffs.set_property("tool_required", True)
    cliffs_message = "but the rocks are too slippery and it becomes impossible without the right tool (a sturdy stick!)."
    cliffs.set_property("search_fail", cliffs_message)

    stick4 = things.Item(
        "stick",
        "a long stick",
        "A sturdy stick to keep balanced on slippery rocks."
    )
    cliffs.add_item(stick4)

    # Characters
    characters = []
    # EXPLORATION
    start_at = cliffs

    for i, filename in enumerate(os.listdir("exploration_personas")):
        if i > 1:
            break
        if filename.endswith(".json"):
            persona = Persona.import_persona("exploration_personas/" + filename)
            character = DiscoveryAgent(persona, "B")
            location = cliffs
            location.add_character(character)
            characters.append(character)
            print(f"Character {character.name} starts at {location.name} and belongs to Group B")
    
    player = characters.pop(0)

    # The Game
    game = DiscoveryGame(start_at, 
                         player, 
                         characters, 
                         custom_actions=None,
                         max_ticks=max_ticks,
                         num_finalists=num_finalists,
                         experiment_name=experiment_name,
                         experiment_id=experiment_id)

    return game
