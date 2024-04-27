# local imports
from . import base
from . import preconditions as P
from .consume import Drink, Eat
from ..things import Character


class Get(base.Action):
    ACTION_NAME = "get"
    ACTION_DESCRIPTION = "Acquire, get, take, pick up an item for personal use and add to inventory."
    ACTION_ALIASES = ["take", "collect", "pick up"]

    def __init__(self, game, command: str, character: Character):
        super().__init__(game)
        self.command = command
        # self.character = self.parser.get_character(command)
        self.character = character
        self.location = self.character.location
        self.item = self.parser.match_item(command, self.location.items)

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * The item must be matched.
        * The character must be at the location
        * The item must be at the location
        * The item must be gettable
        """
        if not self.was_matched(self.character, self.item, "I don't see it."):
            message = f"I don't see this item in {self.location.name}."
            self.parser.fail(self.command, message, self.character)
            return False
        if not self.location.here(self.character):
            message = "{name} is not in {loc}.".format(name=self.character.name, loc=self.location.name)
            self.parser.fail(self.command, message, self.character)
            return False
        if not self.location.here(self.item):
            message = "There is no {name} in {loc}.".format(name=self.item.name, loc=self.location.name)
            self.parser.fail(self.command, message, self.character)
            return False
        if self.item and not self.item.get_property("gettable"):
            message = "{name} is not {property_name}.".format(
                name=self.item.name.capitalize(), property_name="gettable"
            )
            self.parser.fail(self.command, message, self.character)
            return False
        return True

    def apply_effects(self):
        """
        Get's an item from the location and adds it to the character's
        inventory, assuming preconditions are met.
        """
        self.location.remove_item(self.item)
        self.character.add_to_inventory(self.item)
        description = "{character_name} got the {item_name}.".format(
            character_name=self.character.name, item_name=self.item.name
        )
        # self.parser.ok(description)
        self.parser.ok(self.command, description, self.character)
        return True


class Drop(base.Action):
    ACTION_NAME = "drop"
    ACTION_DESCRIPTION = "Drop or remove an item from possession, alternatively described as discarding or eliminating."
    ACTION_ALIASES = ["toss", "get rid of"]

    def __init__(
        self,
        game,
        command: str,
        character: Character
    ):
        super().__init__(game)
        self.command = command
        # self.character = self.parser.get_character(command)
        self.character = character
        self.location = self.character.location
        self.item = self.parser.match_item(command, self.character.inventory)

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * The item must be in the character's inventory
        """
        if not self.was_matched(self.character, self.item, "I don't see it."):
            return False
        if not self.character.is_in_inventory(self.item):
            d = "{character_name} does not have the {item_name}."
            description = d.format(
                character_name=self.character.name, item_name=self.item.name
            )
            self.parser.fail(self.command, description, self.character)
            return False
        return True

    def apply_effects(self):
        """
        Drop removes an item from character's inventory and adds it to the
        current location, assuming preconditions are met
        """
        self.character.remove_from_inventory(self.item)
        self.item.location = self.location
        self.location.add_item(self.item)
        d = "{character_name} dropped the {item_name} in the {location}."
        description = d.format(
            character_name=self.character.name.capitalize(),
            item_name=self.item.name,
            location=self.location.name,
        )
        # self.parser.ok(description)
        self.parser.ok(self.command, description, self.character)
        return True


class Inventory(base.Action):
    ACTION_NAME = "inventory"
    ACTION_DESCRIPTION = "Check personal inventory, a list of items currently held and often referred to as checking belongings."
    ACTION_ALIASES = ["i"]

    def __init__(
        self,
        game,
        command: str,
        character: Character
    ):
        super().__init__(game)
        self.command = command
        # self.character = self.parser.get_character(command)
        self.character = character

    def check_preconditions(self) -> bool:
        if self.character is None:
            return False
        return True

    def apply_effects(self):
        if len(self.character.inventory) == 0:
            description = f"{self.character.name}'s inventory is empty."
            # self.parser.ok(description)
            self.parser.ok(self.command, description, self.character)
        else:
            description = f"{self.character.name}'s inventory contains:\n"
            for item_name in self.character.inventory:
                item = self.character.inventory[item_name]
                description += "* {item}\n".format(item=item.description)
            # self.parser.ok(description)
            self.parser.ok(self.command, description, self.character)
        return True


class Examine(base.Action):
    ACTION_NAME = "examine"
    ACTION_DESCRIPTION = "Closely inspect or look at an object/item to learn more about it, including examining or scrutinizing."
    ACTION_ALIASES = ["look at", "x"]

    def __init__(
        self,
        game,
        command: str,
        character: Character
    ):
        super().__init__(game)
        self.command = command
        # self.character = self.parser.get_character(command)
        self.character = character
        self.matched_item = self.parser.match_item(
            command, self.parser.get_items_in_scope(self.character)
        )

    def check_preconditions(self) -> bool:
        if self.character is None:
            return False
        return True

    def apply_effects(self):
        """The player wants to examine an item"""
        if self.matched_item:
            if self.matched_item.examine_text:
                self.parser.ok(self.command, self.matched_item.examine_text, self.character)
            else:
                self.parser.ok(self.command, self.matched_item.description, self.character)
        else:
            self.parser.ok(self.command, "You don't see anything special.", self.character)
        return True


class Give(base.Action):
    ACTION_NAME = "give"
    ACTION_DESCRIPTION = "Give or transfer something (an item for example) to another individual. Also referred to as handing over."
    ACTION_ALIASES = ["hand", "deliver", "offer"]

    def __init__(self, 
                 game, 
                 command: str,
                 character: Character):
        super().__init__(game)
        self.command = command
        # self.character = self.parser.get_character(command)
        # self.character = character
        give_words = ["give", "hand"]
        command_before_word = ""
        command_after_word = command
        for word in give_words:
            if word in command:
                parts = command.split(word, 1)
                command_before_word = parts[0]
                command_after_word = parts[1]
                break
        # self.giver = self.parser.get_character(command_before_word)
        self.giver = character
        self.recipient = self.parser.get_character(command_after_word, character=None)
        self.item = self.parser.match_item(command, self.giver.inventory)

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * The item must be in the giver's inventory
        * The character must be at the same location as the recipient
        """
        if not self.was_matched(self.giver, self.item, "I don't see it."):
            return False
        if not self.giver.is_in_inventory(self.item):
            return False
        if not self.giver.location.here(self.recipient):
            return False
        return True

    def apply_effects(self):
        """
        Drop removes an item from character's inventory and adds it to the
        current location. (Assumes that the preconditions are met.)
        If the recipient is hungry and the item is food, the recipient will
        eat it.
        If the recipient is thisty and the item is drink, the recipient will
        drink it.
        """
        self.giver.remove_from_inventory(self.item)
        self.recipient.add_to_inventory(self.item)
        description = "{giver} gave the {item_name} to {recipient}".format(
            giver=self.giver.name.capitalize(),
            item_name=self.item.name,
            recipient=self.recipient.name.capitalize(),
        )
        self.parser.ok(self.command, description, self.giver)

        if self.recipient.get_property("is_hungry") and self.item.get_property(
            "is_food"
        ):
            command = "{name} eat {food}".format(
                name=self.recipient.name, food=self.item.name
            )
            eat = Eat(self.game, command, self.recipient)
            eat()

        if self.recipient.get_property("is_thisty") and self.item.get_property(
            "is_drink"
        ):
            command = "{name} drink {drink}".format(
                name=self.recipient.name, drink=self.item.name
            )
            drink = Drink(self.game, command, self.recipient)
            drink()

        return True


class Unlock_Door(base.Action):
    ACTION_NAME = "unlock door"
    ACTION_DESCRIPTION = "Unlock a door that is currently locked so that it may be opened"

    def __init__(self, game, command, character):
        super().__init__(game)
        self.command = command
        # self.character = self.parser.get_character(command)
        self.character = character
        self.key = self.parser.match_item(
            "key", self.parser.get_items_in_scope(self.character)
        )
        self.door = self.parser.match_item(
            "door", self.parser.get_items_in_scope(self.character)
        )

    def check_preconditions(self) -> bool:
        if self.door and self.door.get_property("is_locked") and self.key:
            return True
        else:
            return False

    def apply_effects(self):
        self.door.set_property("is_locked", False)
        # self.parser.ok("Door is unlocked")
        self.parser.ok(self.command, "Door is unlocked", self.character)
        return True
