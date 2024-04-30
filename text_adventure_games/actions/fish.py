# local imports
from text_adventure_games.things.characters import Character
from . import base
from . import preconditions as P
from ..things import Item


class Catch_Fish(base.Action):
    ACTION_NAME = "catch fish"
    ACTION_DESCRIPTION = "Catch fish with a pole. Generally, catch an aquatic animal or creature with a rod."
    ACTION_ALIASES = ["go fishing"]

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        # self.character = self.parser.get_character(command)
        self.command = command
        self.character = character
        self.pond = self.character.location
        self.pole = False
        if " pole" in command or " rod" in command:
            self.pole = self.parser.match_item(
                "pole", self.parser.get_items_in_scope(self.character)
            )
        fish = Item("fish", "a dead fish", "IT SMELLS TERRIBLE.")
        fish.add_command_hint("eat fish")
        fish.set_property("is_food", True)
        fish.set_property(
            "taste", "disgusting! It's raw! And definitely not sashimi-grade!"
        )
        if self.pond and self.pond.has_property("has_fish"):
            self.pond.set_property("has_fish", True)
            self.pond.add_item(fish)

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * There must be a pond
        * The character must be at the pond
        * The character must have a fishing pole in their inventory
        """
        if self.pond and not self.pond.has_property("has_fish"):
            self.parser.fail(self.command, f"{self.character.name} tried to fish in {self.pond.name}. Fish are not found here.", self.character)
            return False
        if not self.was_matched(self.character, self.pond, "There's no body of water here."):
            self.parser.fail(self.command, f"{self.character.name} tried to fish in {self.pond.name}, which might not be a body of water", self.character)
            return False
        if not self.pond.get_property("has_fish"):
            self.parser.fail(self.command, "The body of water has no fish.", self.character)
            return False
        # if not self.character.is_in_inventory(self.pole):
        #     return False
        return True

    def apply_effects(self):
        """
        Effects:
        * Creates a new item for the fish
        * Adds the fish to the character's inventory
        * Sets the 'has_fish' property of the pond to False.
        """
        if not self.pole:
            no_pole = "".join(
                [
                    f"{self.character.name} reaches into the pond and tries to ",
                    "catch a fish with their hands, but the fish are too fast. ",
                    "Try to specify that you want to catch fish with the fishing pole."
                ]
            )
            self.parser.fail(self.command, no_pole, self.character)
            return False

        fish = self.pond.get_item("fish")
        if fish:
            self.pond.set_property("has_fish", False)
            self.pond.remove_item(fish)
            self.character.add_to_inventory(fish)

        d = "".join(
            [
                f"{self.character.name} dips their hook into the pond and ",
                "catches a fish. It might be good to eat!",
            ]
        )
        description = d.format(character_name=self.character.name)
        # self.parser.ok(description)
        self.parser.ok(self.command, description, self.character)
        return True
