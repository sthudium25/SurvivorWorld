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
        idol = Item("idol", "an immunity idol", "THIS IDOL GRANTS YOU IMMUNITY AT THE NEXT VOTE.")
        idol.add_command_hint("keep it a secret from your enemies!")
        self.jungle.set_property("has_idol", True)
        self.jungle.add_item(idol)

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
            self.parser.fail(self.command, "The jungle has no idol.", self.character)
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

        idol = self.jungle.get_item("idol")
        if idol:
            random_number = random.random()
            if random_number < 0.3:
                self.jungle.set_property("has_idol", False)
                self.jungle.remove_item(idol)
                self.character.add_to_inventory(idol)
                self.character.set_property("immune", True)
            else:
                description = """You look around for an idol but found nothing.
                You sense it should be nearby and you can keep on trying! You might have better luck next time!"""
                self.parser.fail(self.command, no_machete, self.character)
                return True
        d = "".join(
            [
                "{character_name} hacks their way into the deep jungle and ",
                "finds an idol near a large tree!",
            ]
        )
        description = d.format(character_name=self.character.name)

        self.parser.ok(self.command, description, self.character)
        return True
