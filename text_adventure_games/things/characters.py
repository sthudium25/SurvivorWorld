from typing import Union
from .base import Thing
from .items import Item
from ..agent.memory_stream import MemoryStream, MemoryType
from ..agent.agent_cognition import act, reflect, impressions, goals, perceive


class Character(Thing):
    """
    This class represents the player and non-player characters (NPC).
    Characters have:
    * A name (can be general like "gravedigger")
    * A description ('You might want to talk to the gravedigger, especially if
      you're looking for a friend. He might be odd but you will find a friend in
      him.')
    * A persona written in the first person ("I am low paid labor in this town.
      I do a job that many people shun because of my contact with death. I am
      very lonely and wish I had someone to talk to who isn't dead.")
    * A location (the place in the game where they currently are)
    * An inventory of items that they are carrying (a dictionary mapping from
      item name to Item instance)
    * TODO: A dictionary of items that they are currently wearing
    * TODO: A dictionary of items that they are currently weilding
    """

    def __init__(
        self, name: str, description: str, persona: str,
    ):
        super().__init__(name, description)
        self.set_property("character_type", "notset")
        self.set_property("is_dead", False)
        self.persona = persona
        self.inventory = {}
        self.location = None
        self.memory = []

    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Character):
            # Don't attempt to compare against unrelated types
            return NotImplemented

        return self.id == other.id

    def to_primitive(self):
        """
        Converts this object into a dictionary of values the can be safely
        serialized to JSON.

        Notice that object instances are replaced with their name. This
        prevents circular references that interfere with recursive
        serialization.
        """
        thing_data = super().to_primitive()
        thing_data['persona'] = self.persona

        inventory = {}
        for k, v in self.inventory.items():
            if hasattr(v, 'to_primitive'):
                inventory[k] = v.to_primitive()
            else:
                inventory[k] = v
        thing_data['inventory'] = inventory

        if self.location and hasattr(self.location, 'name'):
            thing_data['location'] = self.location.name
        elif self.location:
            thing_data['location'] = self.location
        return thing_data

    @classmethod
    def from_primitive(cls, data):
        """
        Converts a dictionary of primitive values into a character instance.

        Notice that the from_primitive method is called for items.
        """
        instance = cls(data['name'], data['description'], data['persona'])
        super().from_primitive(data, instance=instance)
        instance.location = data.get('location', None)
        instance.inventory = {
            k: Item.from_primitive(v) for k, v in data['inventory'].items()
        }
        return instance

    def add_to_inventory(self, item):
        """
        Add an item to the character's inventory.
        """
        if item.location is not None:
            item.location.remove_item(item)
            item.location = None
        self.inventory[item.name] = item
        item.owner = self

    def is_in_inventory(self, item):
        """
        Checks if a character has the item in their inventory
        """
        return item.name in self.inventory

    def remove_from_inventory(self, item):
        """
        Removes an item to a character's inventory.
        """
        item.owner = None
        self.inventory.pop(item.name)


class GenerativeAgent(Character):
    
    def __init__(self, 
                 persona,
                 use_goals: bool = True, 
                 use_impressions: bool = True):
        super().__init__(persona.facts["Name"], persona.description, persona=persona.summary)

        # Cognition settings
        self.use_goals = use_goals
        self.use_impressions = use_impressions

        # Set the Agent's persona, empty impressions, and initialize empty goals:
        self.persona = persona
        if use_impressions:
            self.impressions = impressions.Impressions(self.name, self.id)
        else:
            self.impressions = None
        if use_goals:
            self.goals = goals.Goals(self)
        else:
            self.goals = None

        # Initialize Agent's memory
        self.memory = MemoryStream(self)
        self.last_location_observations = None

    # TODO: this is probably a redundant method than we can delete
    def get_character_summary(self):
        """
        Get a summary of the traits for this agent

        Returns:
            str: a standard summary paragraph for this agent
        """
        summary = self.persona.get_personal_summary()
        summary += self.get_alliance_summary()
        return summary

    def engage(self, game) -> Union[str, int]:
        """
        wrapper method for all agent cognition: perceive, retrieve, act, reflect, set goals

        Args:
            game (Game): the current game object

        Returns:
            Union[str, int]: An action string or int flag -999 to trigger skipped action
        """
        # If this is the end of a round, force reflection
        if game.tick == game.max_ticks_per_round - 1:
            # print(f"{self.name} has {len(self.memory.get_observations_by_type(3))} existing reflections")
            reflect.reflect(game, self)  # TODO: Evaluation of goals should be triggered within reflection
            if self.use_goals:
                self.goals.gpt_generate_goals(game)
            return -999

        # Percieve the agent's surroundings 
        self.perceive(game)

        # Update this agent's impressions of characters in the same location
        if self.use_impressions:
            self.update_character_impressions(game)

        # act accordingly
        return act.act(game, self)
    
    def perceive(self, game):
        perceive.percieve_location(game, self)
        self.chars_in_view = self.get_characters_in_view(game)
                
    def get_characters_in_view(self, game):
        # NOTE: it would be nicer to have characters listed in the location object
        # however this is more state to maintain.
        """
        Given a character, identifies the other characters in the game that are in the same location

        Args:
            character (Character): the current character

        Returns:
            list: characters in view of the current character
        """
        chars_in_view = []
        for char in game.characters.values():
            if char.location.id == self.location.id and char.id != self.id:
                chars_in_view.append(char)

        return chars_in_view

    def update_character_impressions(self, game):
        """
        Update this agent's impression of nearby characters

        Args:
            game (Game): the current game object
        """
        for target in self.get_characters_in_view(game):
            self.impressions.update_impression(game, self, target)
