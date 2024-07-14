# local imports
from text_adventure_games.things.characters import Character
from . import base
from .things import Drop
from . import preconditions as P


class Attack(base.Action):
    ACTION_NAME = "attack"
    ACTION_DESCRIPTION = "Attack someone or something with a weapon or initiate combat or physical confrontation, also known as striking or hitting."
    ACTION_ALIASES = ["hit"]

    def __init__(
        self,
        game,
        command: str,
        character: Character
    ):
        super().__init__(game)
        self.command = command
        # self.character = character
        attack_words = ["attack", "hit", "strike", "punch", "thwack"]
        command_before_word = ""
        command_after_word = command
        for word in attack_words:
            if word in command:
                parts = command.split(word, 1)
                command_before_word = parts[0]
                command_after_word = parts[1]
                break
        # self.attacker = self.parser.get_character(command_before_word)
        self.attacker = character
        self.victim = self.parser.get_character(command_after_word, character=None)
        self.weapon = self.parser.match_item(command, self.attacker.inventory)

    def check_preconditions(self) -> bool:
        """
        Preconditions:
        * There must be an attacker and a victim
        * They must be in the same location
        * There must be a matched weapon
        * The attacker must have the weapon in their inventory
        * The weapon have the property 'is_weapon'
        * The victim must not already be dead or unconscious
        """
        if not self.was_matched(self.attacker, self.attacker):
            description = "The attacker couldn't be found."
            self.parser.fail(self.command, description, self.attacker)
            return False
        if not self.was_matched(self.attacker, self.victim):
            description = f"{self.victim} could not be found"
            self.parser.fail(self.command, description, self.attacker)
            return False
        if not self.attacker.location.here(self.victim):
            description = f"{self.attacker.name} tried to attack {self.victim.name} but {self.victim.name} is NOT found at {self.attacker.location}"
            self.parser.fail(description)
            return False
        if not self.was_matched(
            self.attacker,
            self.weapon,
            error_message="{name} doesn't have a weapon.".format(
                name=self.attacker.name
            ),
            describe_error=False
        ):
            self.parser.fail(self.command, description, self.attacker)
            return False
        if not self.attacker.is_in_inventory(self.weapon):
            description = f"{self.attacker.name} doesn't have the {self.weapon.name}."
            self.parser.fail(self.command, description, self.attacker)
            return False
        if not self.weapon.get_property("is_weapon"):
            description = "{item} is not a weapon".format(item=self.weapon.name)
            self.parser.fail(self.command, description, self.attacker)
            return False
        if self.victim.get_property("is_unconscious"):
            description = "{name} is already unconscious".format(name=self.victim.name)
            self.parser.fail(self.command, description, self.attacker)
            return False
        if self.victim.get_property("is_dead"):
            description = "{name} is already dead".format(name=self.victim.name)
            self.parser.fail(self.command, description, self.attacker)
            return False
        return True

    def apply_effects(self):
        """
        Effects:
        * If the victim is not invulerable to attacks
        ** Knocks the victim unconscious
        ** The victim drops all items in their inventory
        * If the weapon is fragile then it breaks
        """
        description = "{attacker} attacked {victim} with the {weapon}.".format(
            attacker=self.attacker.name,
            victim=self.victim.name,
            weapon=self.weapon.name,
        )
        self.parser.ok(self.command, description, self.attacker)

        if self.weapon.get_property("is_fragile"):
            description = "The fragile weapon broke into pieces."
            self.attacker.remove_from_inventory(self.weapon)
            self.parser.ok(self.command, description, self.attacker)

        if self.victim.get_property("is_invulerable"):
            description = "The attack has no effect on {name}.".format(
                name=self.victim.name
            )
            self.parser.ok(self.command, description, self.attacker)
        else:
            # the victim is knocked unconscious
            self.victim.set_property("is_unconscious", True)
            description = "{name} was knocked unconscious.".format(
                name=self.victim.name.capitalize()
            )
            self.parser.ok(self.command, description, self.attacker)

            # the victim drops their inventory
            items = list(self.victim.inventory.keys())
            for item_name in items:
                item = self.victim.inventory[item_name]
                command = "{victim} drop {item}".format(
                    victim=self.victim.name, item=item_name
                )
                drop = Drop(self.game, command)
                if drop.check_preconditions():
                    drop.apply_effects()
        return True
