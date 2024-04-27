# local imports
from ..things.characters import Character
from . import base
from . import preconditions as P


class Eat(base.Action):
    ACTION_NAME = "eat"
    ACTION_DESCRIPTION = "Ingest food items for nourishment."

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        self.command = command
        self.character = character
        self.item = self.parser.match_item(
            command, self.parser.get_items_in_scope(self.character)
        )

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * There must be a matched item
        * The item must be food
        * The food must be in character's inventory
        """
        if not self.was_matched(self.character, self.item):
            return False
        elif not self.item.get_property("is_food"):
            description = "That's not edible."
            self.parser.fail(self.command, description, self.character)
            return False
        elif not self.character.is_in_inventory(self.item):
            description = "You don't have it."
            self.parser.fail(self.command, description, self.character)
            return False
        return True

    def apply_effects(self):
        """
        Effects:
        * Removes the food from the inventory so that it has been consumed.
        * Causes the character's hunger to end
        * Describes the taste (if the "taste" property is set)
        * If the food is poisoned, it causes the character to die.
        """
        self.character.remove_from_inventory(self.item)
        self.character.set_property("is_hungry", False)
        description = "{name} eats the {food}.".format(
            name=self.character.name.capitalize(), food=self.item.name
        )

        if self.item.get_property("taste"):
            description += " It tastes {taste}".format(
                taste=self.item.get_property("taste")
            )

        if self.item.get_property("is_poisonous"):
            self.character.set_property("is_dead", True)
            description += " The {food} is poisonous. {name} died.".format(
                food=self.item.name, name=self.character.name.capitalize()
            )
        # self.parser.ok(description)
        self.parser.ok(self.command, description, self.character)
        return True


class Drink(base.Action):
    ACTION_NAME = "drink"
    ACTION_DESCRIPTION = "Drink a liquid."

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        # self.character = self.parser.get_character(command)
        self.command = command
        self.character = character
        self.item = self.parser.match_item(
            command, self.parser.get_items_in_scope(self.character)
        )

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * There must be a matched item
        * The item must be a drink
        * The drink must be in character's inventory
        """
        if not self.was_matched(self.character, self.item):
            return False
        elif not self.item.get_property("is_drink"):
            description = "That's not drinkable."
            self.parser.fail(self.command, description, self.character)
            return False
        elif not self.character.is_in_inventory(self.item):
            description = "You don't have it."
            # self.parser.fail(description)
            self.parser.fail(self.command, description, self.character)
            return False
        return True

    def apply_effects(self):
        """
        Effects:
        * Removes the drink from the inventory so that it has been consumed.
        * Causes the character's thirst to end
        * Describes the taste (if the "taste" property is set)
        * If the drink is poisoned, it causes the character to die.
        """
        self.character.remove_from_inventory(self.item)
        self.character.set_property("is_thirsty", False)
        description = "{name} drinks the {drink}.".format(
            name=self.character.name.capitalize(), drink=self.item.name
        )
        # self.parser.ok(description)
        self.parser.ok(self.command, description, self.character)

        if self.item.get_property("taste"):
            description = " It tastes {taste}".format(
                taste=self.item.get_property("taste")
            )
            # self.parser.ok(description)
            self.parser.ok(self.command, description, self.character)

        if self.item.get_property("is_poisonous"):
            self.character.set_property("is_dead", True)
            description = "The {drink} is poisonous. {name} died.".format(
                drink=self.item.name, name=self.character.name.capitalize()
            )
            # self.parser.ok(description)
            self.parser.ok(self.command, description, self.character)

        if self.item.get_property("is_alcohol"):
            self.character.set_property("is_drink", True)
            description = "{name} is now drunk from {drink}.".format(
                drink=self.item.name, name=self.character.name.capitalize()
            )
            # self.parser.ok(description)
            self.parser.ok(self.command, description, self.character)
        return True


class Light(base.Action):
    ACTION_NAME = "light"
    ACTION_DESCRIPTION = "Ignite something flammable like a lamp or a candle. Also includes turning on a light"

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        # self.character = self.parser.get_character(command)
        self.command = command
        self.character = character
        self.item = self.parser.match_item(
            command, self.parser.get_items_in_scope(self.character)
        )

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * There must be a matched item
        * The item must be in character's inventory
        * The item must be lightable
        """
        if not self.was_matched(self.character, self.item):
            return False
        if not self.is_in_inventory(self.character, self.item):
            return False
        if not self.item.get_property("is_lightable"):
            description = "That's not something that can be lit."
            self.parser.fail(self.command, description, self.character)
            return False
        if self.item.get_property("is_lit"):
            description = "It is already lit."
            self.parser.fail(self.command, description, self.character)
            return False
        return True

    def apply_effects(self):
        """
        Effects:
        * Changes the state to lit
        """
        self.item.set_property("is_lit", True)
        description = "{name} lights the {item}. It glows.".format(
            name=self.character.name, item=self.item.name
        )
        # self.parser.ok(description)
        self.parser.ok(self.command, description, self.character)
        return True
