# local imports
from text_adventure_games.agent.memory_stream import MemoryType
from text_adventure_games.things.characters import Character
from . import base
from ..things import Item
from text_adventure_games.utils.general import enumerate_dict_options, get_logger_extras
import random


class Search_Idol(base.Action):
    ACTION_NAME = "search idol"
    ACTION_DESCRIPTION = "Look for an idol. Typically requires a tool in order to be successful."
    ACTION_ALIASES = ["look for idol", "search for idol", "find idol"]

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        self.valid_idol_locations = [loc for loc in game.locations.values() if loc.get_property("has_idol")]
        self.command = command
        self.character = character
        self.location = self.character.location
        self.tool_required = self.location.get_property("tool_required")
        self.tool = False
        if " machete" in command:
            self.tool = self.parser.match_item(
                "machete", self.parser.get_items_in_scope(self.character)
            )
        if " stick" in command:
            self.tool = self.parser.match_item(
                "stick", self.parser.get_items_in_scope(self.character)
            )

        # EXPLORATION
        self.clue = self.parser.match_item(
            "idol clue", self.parser.get_items_in_scope(self.character)
        )

    def _log_found_idol(self, message):
        extras = get_logger_extras(self.game, self.character)
        extras["type"] = "Idol"
        self.game.logger.debug(msg=message, extra=extras)
        
    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * The character must be at the jungle
        * The character must have a machete in their inventory
        """
        if not self.location.get_property("has_idol"):
            description = f"You look around, but cannot find an idol in the {self.location.name}. "
            if self.location.get_property("idol_found"):
                description += self.location.get_property("found_message")
            else:
                description += "This area seems unlikely to have one."
            print("DEBUG: idol search failure due to: ", description)
            self.parser.fail(self.command, description, self.character)
            return False
        if not self.location.here(self.character):
            print("DEBUG: idol search failure due to character in wrong place")
            self.parser.fail(self.command, "You get the feeling there won't be an idol at this location", self.character)
            return False  
        if not self.tool and self.tool_required:
            print("DEBUG: idol search failure due to lack of proper tools")
            no_tool = f"{self.character.name} looks around the {self.location.name} "

            if self.location.id in [loc.id for loc in self.valid_idol_locations]:
                no_tool += self.location.get_property("search_fail")
            else:
                no_tool += "and sense that there probably is no idol hidden here."

            self.parser.fail(self.command, no_tool, self.character)
            return False
        if self.location.name == "rocky shore":
            # Fail every other round
            if self.game.round % 2 == 0:
                dangerous = "".join([
                    f"{self.character.name} looks out at the {self.location.name} ",
                    self.location.get_property("search_fail"),
                    f"{self.character.name} could not search the rocky shore on an even numbered round. ",
                    "What pattern does the failure message above suggest is the correct time to search for this idol?"
                ])
                print("DEBUG: idol search failure due to an even round at the rocky shore")
                self.parser.fail(self.command, dangerous, self.character)
            return False
        return True

    def apply_effects(self):
        """
        Effects:
        * Randomized success of finding an idol
        * If found, adds idol to player inventory
        * Player is immune until next round.
        """

        random_number = random.random()
        threshold_pad = self.character.get_idol_searches() * 0.1
        print("Search random number: ", random_number)
        print("Searcher odds padding: ", threshold_pad)
        if random_number < (0.7 + threshold_pad) or (random_number < (0.8 + threshold_pad) and self.clue):
            idol = Item("idol", "an immunity idol", "THIS IDOL SCORES POINTS FOR YOUR TEAM!")
            idol.add_command_hint("keep it a secret from your enemies!")
            self.character.add_to_inventory(idol)
            self.character.set_property("immune", True)
            self.location.set_property("has_idol", False)
            self.location.set_property("idol_found", True)

            idol_value = 100 - self.game.total_ticks
            self.character.update_score(idol_value)
            print(f"DEBUG: idol search successful! {self.character.name} found it at the {self.location.name}")
            self._log_found_idol(message=f"Found idol at: {self.location.name}; worth points: {idol_value}")
        else:
            description = "".join([
                "You look around for an idol but found nothing. It seems like this is the correct way to search. ",
                "You sense it should be nearby and you can keep on trying! You might have better luck next time!"
            ])

            self.parser.fail(self.command, description, self.character)
            self.character.increment_idol_search()
            return True
        found = "".join(
            [
                "{character_name} searches around in the {location} and ",
                "finds an idol! They have scored {value} points for your team!",
            ]
        )
        description = found.format(character_name=self.character.name, 
                                   location=self.location.name,
                                   value=idol_value or (100 - self.game.total_ticks))

        # self.parser.ok(self.command, description, self.character)

        idol_kwds = self.parser.extract_keywords(description)

        for c in list(self.game.characters.values()):
            c.memory.add_memory(round=self.game.round,
                                tick=self.game.tick,
                                description=description,
                                keywords=idol_kwds,
                                location=self.character.location.name,
                                success_status=True,
                                memory_importance=10,
                                memory_type=MemoryType.ACTION.value,
                                actor_id=self.character.id)
        return True


class Read_Clue(base.Action):
    ACTION_NAME = "read clue"
    ACTION_DESCRIPTION = "Examine the clue for details on the idol's location."
    ACTION_ALIASES = ["examine clue", "read clue", "read idol clue"]

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        self.command = command
        self.character = character
        self.clue = self.parser.match_item(
            "idol clue", self.parser.get_items_in_scope(self.character)
        )

    def _log_clue(self, game, character, message):
        extras = get_logger_extras(game, character)
        extras["type"] = "Clue"
        game.logger.debug(msg=message, extra=extras)

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * The character must have the clue nearby
        """
        if not self.clue:
            self.parser.fail(self.command, "There is no idol clue at this location", self.character)
            return False
        # print("Clue was found: ", self.clue.name, ". Description: ", self.clue.description)
        return True

    def apply_effects(self):
        """
        Effects:
        * Let agent know details about the idol
        """
        d = "".join(
            [
                "{character_name} reads the idol clue to themself:\n",
                self.clue.get_property("clue_content"),
                "\nTo share this information with your teammate, you must talk to them."
            ]
        )
        description = d.format(character_name=self.character.name)
        action_statement, action_importance, action_keywords = self.parser.summarise_and_score_action(description=description, 
                                                                                                      thing=self.character,
                                                                                                      command=self.command,
                                                                                                      needs_summary=False)
        self.character.memory.add_memory(round=self.game.round,
                                         tick=self.game.tick,
                                         description=action_statement,
                                         keywords=action_keywords,
                                         location=self.character.location.name,
                                         success_status=True,
                                         memory_importance=action_importance,
                                         memory_type=MemoryType.ACTION.value,
                                         actor_id=self.character.id)

        # self.parser.ok(self.command, description, self.character)
        self._log_clue(self.game, self.character, f"{self.character.name} read the clue.")
        return True
