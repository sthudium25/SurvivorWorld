# local imports
from text_adventure_games.things.characters import Character
from . import base
from ..things import Item
import random


class Search_Idol(base.Action):
    ACTION_NAME = "search idol"
    ACTION_DESCRIPTION = "Look for an idol in the jungle. Can only be done with a machete."
    ACTION_ALIASES = ["look for idol", "search for idol", "find idol"]

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        self.command = command
        self.character = character
        self.jungle = game.locations.get("Jungle", None)
        self.machete = False
        if " machete" in command:
            self.machete = self.parser.match_item(
                "machete", self.parser.get_items_in_scope(self.character)
            )
        # EXPLORATION
        self.clue = self.parser.match_item(
                "idol clue", self.parser.get_items_in_scope(self.character)
            )
        

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * The character must be at the jungle
        * The character must have a machete in their inventory
        """
        if not self.jungle:
            self.parser.fail(self.command, "You get the feeling there won't be an idol at this location", self.character)
            return False
        if not self.jungle.here(self.character):
            self.parser.fail(self.command, "You get the feeling there won't be an idol at this location", self.character)
            return False
        if not self.jungle.get_property("has_idol"):
            self.parser.fail(self.command, "The jungle has no idol. It looks like someone already took it.", self.character)
            return False
        return True

    def apply_effects(self):
        """
        Effects:
        * Randomized success of finding an idol
        * If found, adds idol to player inventory
        * Player is immune until next round.
        """
        # TODO: maybe add use idol function

        if not self.machete:
            no_machete = "".join(
                [
                    f"{self.character.name} looks around the jungle ",
                    "but the vines get in the way and it becomes impossible without the right tool (a machete!).",
                ]
            )
            self.parser.fail(self.command, no_machete, self.character)
            return False

        random_number = random.random()
        if random_number < 0.3 or (random_number < 0.5 and self.clue):
            idol = Item("idol", "an immunity idol", "THIS IDOL GRANTS YOU IMMUNITY AT THE NEXT VOTE.")
            idol.add_command_hint("keep it a secret from your enemies!")
            self.character.add_to_inventory(idol)
            self.character.set_property("immune", True)
            self.jungle.set_property("has_idol", False)
        else:
            description = """You look around for an idol but found nothing.
            You sense it should be nearby and you can keep on trying! You might have better luck next time!"""
            self.parser.fail(self.command, description, self.character)
            return True
        d = "".join(
            [
                "{character_name} hacks their way into the deep jungle and ",
                "finds an idol near a large tree! You are immune next round.",
            ]
        )
        description = d.format(character_name=self.character.name)

        self.parser.ok(self.command, description, self.character)
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
        

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * The character must have the clue nearby
        """
        if not self.clue:
            self.parser.fail(self.command, "There is no idol clue at this location", self.character)
            return False
        return True

    def apply_effects(self):
        """
        Effects:
        * Let agent know details about the idol
        """
        d = "".join(
            [
                "{character_name} reads the idol clue out loud: ",
                "'The idol can be found by searching the jungle with a machete.' ",
                "'You can fail this action but keep trying as long as you have a machete and are in the jungle!'",
            ]
        )
        description = d.format(character_name=self.character.name)

        self.parser.ok(self.command, description, self.character)
        return True