"""The Parser

The parser is the module that handles the natural language understanding in
the game. The players enter commands in text, and the parser interprets them
and performs the actions that the player intends.  This is the module with
the most potential for improvement using modern natural language processing.
The implementation that I have given below only uses simple keyword matching.
"""

import inspect
import textwrap

from .things import Character, Item, Location
from . import actions, blocks


class Parser:
    """
    The Parser is the class that handles the player's input.  The player
    writes commands, and the parser performs natural language understanding
    in order to interpret what the player intended, and how that intent
    is reflected in the simulated world.
    """

    def __init__(self, game):
        # A list of the commands that the player has issued,
        # and the respones given to the player.
        self.command_history = []

        # Build default scope of actions
        self.actions = game.default_actions()

        # Build default scope of blocks
        self.blocks = game.default_blocks()

        # A pointer to the game.
        self.game = game
        self.game.parser = self

    def ok(self, description: str):
        """
        In the next homework, we'll replace this with a call to the OpenAI API
        in order to create more evocative descriptions.
        """
        print(Parser.wrap_text(description))
        self.add_description_to_history(description)

    def fail(self, description: str):
        """
        In the next homework, we'll replace this with a call to the OpenAI API
        in order to create more evocative descriptions.
        """
        print(Parser.wrap_text(description))

    @staticmethod
    def wrap_text(text: str, width: int = 80) -> str:
        """
        Keeps text output narrow enough to easily be read
        """
        lines = text.split("\n")
        wrapped_lines = [textwrap.fill(line, width) for line in lines]
        return "\n".join(wrapped_lines)

    def add_command_to_history(self, command: str):
        message = {"role": "user", "content": command}
        self.command_history.append(message)
        # CCB - todo - manage command_history size

    def add_description_to_history(self, description: str):
        message = {"role": "assistant", "content": description}
        self.command_history.append(message)
        # CCB - todo - manage command_history size

    def add_action(self, action: actions.Action):
        """
        Add an Action class to the list of actions a parser can use
        """
        self.actions[action.action_name()] = action

    def add_block(self, block):
        """
        Adds a block class to the list of blocks a parser can use. This is
        primarily useful for loading game states from a save.
        """
        self.blocks[block.__class__.__name__] = block

    def init_actions(self):
        self.actions = {}
        for member in dir(actions):
            attr = getattr(actions, member)
            if inspect.isclass(attr) and issubclass(attr, actions.Action):
                # dont include base class
                if not attr == actions.Action:
                    self.add_action(attr)

    def determine_intent(self, command: str):
        """
        This function determines what command the player wants to do.
        Here we have implemented it with a simple keyword match. Later
        we will use AI to do more flexible matching.
        """
        # check which character is acting (defaults to the player)
        character = self.get_character(command)
        command = command.lower()
        if "," in command:
            # Let the player type in a comma separted sequence of commands
            return "sequence"
        elif self.get_direction(command, character.location):
            # Check for the direction intent
            return "direction"
        elif command == "look" or command == "l":
            # when the user issues a "look" command, re-describe what they see
            return "describe"
        elif "examine " in command or command.startswith("x "):
            return "examine"
        elif "take " in command or "get " in command:
            return "take"
        elif "light" in command:
            return "light"
        elif "drop " in command:
            return "drop"
        elif (
            "eat " in command
            or "eats " in command
            or "ate " in command
            or "eating " in command
        ):
            return "eat"
        elif "drink" in command:
            return "drink"
        elif "give" in command:
            return "give"
        elif "attack" in command or "hit " in command or "hits " in command:
            return "attack"
        elif "inventory" in command or command == "i":
            return "inventory"
        elif "quit" in command:
            return "quit"
        else:
            for _, action in self.actions.items():
                special_command = action.action_name()
                if special_command in command:
                    return action.action_name()
        return None

    def parse_action(self, command: str) -> actions.Action:
        """
        Routes an action described in a command to the right action class for
        performing the action.
        """
        command = command.lower().strip()
        if command == "":
            return None
        intent = self.determine_intent(command)
        if intent in self.actions:
            action = self.actions[intent]
            return action(self.game, command)
        elif intent == "direction":
            return actions.Go(self.game, command)
        elif intent == "take":
            return actions.Get(self.game, command)
        self.fail(f"No action found for {command}")
        return None

    def parse_command(self, command: str):
        # print("\n>", command, "\n", flush=True)
        # add this command to the history
        self.add_command_to_history(command)
        action = self.parse_action(command)
        if not action:
            self.fail("I'm not sure what you want to do.")
        else:
            action()

    @staticmethod
    def split_command(command: str, keyword: str) -> tuple[str, str]:
        """
        Splits the command string into two parts based on the keyword.

        Args:
        command (str): The command string to be split.
        keyword (str): The keyword to split the command string around.

        Returns:
        tuple: A tuple containing the part of the command before the keyword and the part after.
        """
        command = command.lower()
        keyword = keyword.lower()
        # Find the position of the keyword in the command
        keyword_pos = command.find(keyword)

        # If the keyword is not found, return the entire command and an empty string
        if keyword_pos == -1:
            return (command, "")

        # Split the command into two parts
        before_keyword = command[:keyword_pos]
        after_keyword = command[keyword_pos + len(keyword) :]

        return (before_keyword, after_keyword)

    def get_character(self, command: str) -> Character:
        """
        This method tries to match a character's name in the command.
        If no names are matched, it returns the default value.
        """
        command = command.lower()
        # matched_character_name = ""  # JD logical change
        for name in self.game.characters.keys():
            if name.lower() in command:
                return self.game.characters[name]
        return self.game.player

    def get_character_location(self, character: Character) -> Location:
        return character.location

    def match_item(self, command: str, item_dict: dict[str, Item]) -> Item:
        """
        Check whether the name any of the items in this dictionary match the
        command. If so, return Item, else return None.
        """
        for item_name in item_dict:
            if item_name in command:
                item = item_dict[item_name]
                return item
        return None

    def get_items_in_scope(self, character=None) -> dict[str, Item]:
        """
        Returns a list of items in character's location and in their inventory
        """
        if character is None:
            character = self.game.player
        items_in_scope = {}
        for item_name in character.location.items:
            items_in_scope[item_name] = character.location.items[item_name]
        for item_name in character.inventory:
            items_in_scope[item_name] = character.inventory[item_name]
        return items_in_scope

    def get_direction(self, command: str, location: Location = None) -> str:
        """
        Converts aliases for directions into its primary direction name.
        """
        command = command.lower()
        if command == "n" or "north" in command:
            return "north"
        if command == "s" or "south" in command:
            return "south"
        if command == "e" or "east" in command:
            return "east"
        if command == "w" or "west" in command:
            return "west"
        if command.endswith("go up"):
            return "up"
        if command.endswith("go down"):
            return "down"
        if command.endswith("go out"):
            return "out"
        if command.endswith("go in"):
            return "in"
        if location:
            for exit in location.connections.keys():
                if exit.lower() in command:
                    return exit
        return None
