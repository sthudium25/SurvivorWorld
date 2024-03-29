from .base import Thing
from .items import Item
from .locations import Location
from ..gpt.agent_kani import AgentKani
from ..gpt.gpt_helpers import gpt_get_action_importance
from ..utils.general import (parse_location_description, 
                             find_difference_in_dict_lists)
from ..agent.memory_stream import MemoryStream, MemoryType
from ..agent.agent_cognition import act


class Character(Thing):
    """
    This class represents the player and non-player characters (NPC).
    Characters have:
    * A name (cab be general like "gravedigger")
    * A description ('You might want to talk to the gravedigger, specially if
      your looking for a friend, he might be odd but you will find a friend in
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
    
    def __init__(self, persona):
        super().__init__(persona.facts["Name"], persona.description, persona=persona.summary)

        # Set the Agent's persona and initialize empty goals:
        self.persona = persona
        self.goals = ""

        # Initialize Agent's memory
        self.memory = MemoryStream(self)
        self.last_location_observations = None

    def get_character_summary(self):
        """
        Get a summary of the traits for this agent

        Returns:
            str: a standard summary paragraph for this agent
        """
        summary = self.persona.get_personal_summary()
        summary += self.get_alliance_summary()
        return summary

    def engage(self, game, round, tick, 
               # vote
               ):
        """
        wrapper method for all agent cognition: perceive, retrieve, act, reflect, set goals

        Args:
            game (games.Game): The current game instance
            round (int): the current round or episode
            tick (_type_): the current time tick within the round

        Returns:
            str: an action
        """
        self.percieve_location(game)
        return act.act(game, self)
 
    # TODO: move perceive into an "agent_cognition" module
    def perceive(self, game):
        # Collect the latest information about the location
        location_description = game.describe()
        return location_description
    
    def percieve_location(self, game):
        """
        Gather rudimentary information about the current location of the Agent
        and store these observations as new memories (of type MemoryType.ACTION).

        Args:
            game (games.Game): the current game object
        """
        location_description = self.perceive(game)
        location_observations = parse_location_description(location_description)

        # check for differences between observations
        diffs_perceived = find_difference_in_dict_lists(self.last_location_observations,
                                                        location_observations)

        # Replace the last perception with the current one
        self.last_location_observations = location_observations.copy()

        # Create new observations from the differences
        for observations in diffs_perceived.values():
            print(f"{self.name} sees: {observations}")
            for statement in observations:
                # TODO: "create_action_statement" method is awkward as part of the Parser class
                action_statement = game.parser.create_action_statement(command="describe",
                                                                       description=statement,
                                                                       character=self)
                
                importance_score = gpt_get_action_importance(action_statement,
                                                             game.parser.client, 
                                                             game.parser.model, 
                                                             max_tokens=10)
                keywords = game.parser.extract_keywords(action_statement)

                self.memory.add_memory(description=action_statement,
                                       keywords=keywords,
                                       location=self.location,
                                       success_status=True,
                                       memory_importance=importance_score,
                                       memory_type=MemoryType.ACTION)
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
            if char.location.id == self.location.id:
                chars_in_view.append(char)

        return chars_in_view

    # def reflect(self):
    #     # Look back at observations from this round
    #     pass

    def act(self):
        # Intent determination here?
        pass
