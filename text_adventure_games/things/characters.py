import os
from typing import List, Union

# local imports
from .base import Thing
from .items import Item
from ..agent.memory_stream import MemoryStream, MemoryType
from ..agent.agent_cognition.act import Act
from ..agent.agent_cognition.reflect import reflect 
from ..agent.agent_cognition.impressions import Impressions
from ..agent.agent_cognition.goals import Goals
from ..agent.agent_cognition.perceive import percieve_location
from ..gpt.gpt_helpers import context_list_to_string

# Used to map group to use_goals and use_impressions
GROUP_MAPPING = {"A": (False, False),
                 "B": (True, False),
                 "C": (False, True),
                 "D": (True, True),
                 "E": (False, False)}


class Character(Thing):
    """
    This class represents the player and non-player characters (NPC).
    Characters have:
    * A name (can be general like "gravedigger")
    * A description ('You might want to talk to the gravedigger, especially if
      you're looking for a friend. He might be odd but you will find a friend in
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

    def get_item_by_name(self, item_name):
        """
        Get an item using its name.
        """
        return self.inventory.get(item_name, None)


class GenerativeAgent(Character):
    
    def __init__(self, 
                 persona,
                 group: str = "D"):
        super().__init__(persona.facts["Name"], persona.description, persona=persona.summary)

        # Cognition settings
        self.group = group
        self.use_goals, self.use_impressions = GROUP_MAPPING[self.group]

        # Set the Agent's persona, empty impressions, and initialize empty goals:
        self.persona = persona
        if self.use_impressions:
            self.impressions = Impressions(self.name, self.id)
        else:
            self.impressions = None
        if self.use_goals:
            self.goals = Goals(self)
        else:
            self.goals = None

        # Initialize Agent's memory
        self.memory = MemoryStream(self)
        self.last_location_observations = None

        # Track last conversation participant
        self.last_talked_to = None

        # Track proper idol searches
        self.idol_search_count = 0

    def set_dialogue_participant(self, talked_to):
        if not talked_to:
            self.last_talked_to = None
        elif isinstance(talked_to, Character):    
            self.last_talked_to = talked_to
        else:
            raise ValueError(f"{talked_to} is invalid.")
    
    def get_last_dialogue_target(self):
        return self.last_talked_to

    def _parse_perceptions(self):
        perception_descriptions = []
        for ptype, percept in self.last_location_observations.items():
            if len(percept) == 1:
                if percept[0].startswith("No "):
                    perception_descriptions.append(f"{self.name} has no {ptype}.")
                else:
                    perception_descriptions.append(percept[0])
            else:
                # Find the common prefix and then append the varying parts
                common_prefix = os.path.commonprefix(percept)
                if common_prefix:
                    # Strip common prefix from each entry and capitalize the first character
                    unique_parts = [p[len(common_prefix):].capitalize() for p in percept]
                    perception_descriptions.append(f"{common_prefix.strip()}: {', '.join(unique_parts)}")
                else:
                    # If no common prefix, join with 'or'
                    perception_descriptions.append(', '.join(percept))

        return context_list_to_string(perception_descriptions, sep="\n")

    def get_standard_info(self, game, include_goals=True, include_perceptions=True):
        """
        Get standard context for this agent
        Includes: world info, persona summary, and (if invoked) goals

        Returns:
            str: a standard summary paragraph for this agent and the world.
        """
        summary = f"WORLD INFO: {game.world_info}\n"
        summary += f"You are {self.persona.get_personal_summary()}.\n"
        if self.use_goals and include_goals:
            goals = self.get_goals(round=game.round, as_str=True)
            if goals:
                summary += f"Your current GOALS:\n{goals}\n"
        if include_perceptions and self.last_location_observations:
            perceptions = self._parse_perceptions()
            if perceptions:
                summary += f"Your current perceptions are:\n{perceptions}\n"
        return summary
    
    def get_goals(self, round=-1, priority="all", as_str=False):
        if self.use_goals:
            return self.goals.get_goals(round=round, priority=priority, as_str=as_str)
        else:
            return None
        
    def get_goal_scores(self, round=-1, priority="all", as_str=False):
        if self.use_goals:
            return self.goals.get_goal_scores(round=round, priority=priority, as_str=as_str)
        else:
            return None

    def generate_goals(self, game):
        # if this is the start of a round, set up the goals:
        if game.tick == 0 and self.use_goals: 
            # print(f"Setting goal for {self.name}")
            self.goals.gpt_generate_goals(game)

    def engage(self, game) -> Union[str, int]:
        """
        wrapper method for all agent cognition: perceive, retrieve, act, reflect, set goals

        Args:
            game (Game): the current game object

        Returns:
            Union[str, int]: An action string or int flag -999 to trigger skipped action
        """

        # If this is the end of a round, force reflection
        if game.tick == (game.max_ticks_per_round - 1):
            reflect(game, self) 
            if self.use_goals:
                self.goals.evaluate_goals(game)
            return -999

        # Percieve the agent's surroundings 
        self.perceive(game)

        # Update this agent's impressions of characters in the same location
        if self.use_impressions:
            self.update_character_impressions(game)

        # act accordingly
        return Act(game, self).act()
    
    def perceive(self, game):
        percieve_location(game, self)
        self.chars_in_view = self.get_characters_in_view(game)
                
    def get_characters_in_view(self, game):
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

    def to_primitive(self):
        thing_data = super().to_primitive()

        thing_data['memory_stream'] = self.memory.get_observations_after_round(0, True)

        if self.goals:
            thing_data['goals'] = self.goals.get_goals()

        if self.impressions:
            thing_data['impressions'] = self.impressions.impressions

    def get_idol_searches(self):
        return self.idol_search_count

    def increment_idol_search(self):
        self.idol_search_count += 1


class DiscoveryAgent(GenerativeAgent):
    def __init__(self, 
                 persona,
                 group: str = "D"):
        super().__init__(persona, group)
        self.score = 0

    def set_teammates(self, members: List[GenerativeAgent]):
        self.teammates = [m for m in members if isinstance(m, GenerativeAgent) and m.id != self.id]

    def get_teammates(self, names_only=False, as_str=False):
        if names_only:
            if as_str:
                return ", ".join([agent.name for agent in self.teammates])
            else:
                return [agent.name for agent in self.teammates]
        else:
            return self.teammates
        
    def update_score(self, add_on: int):
        self.score += add_on

    def engage(self, game) -> Union[str, int]:
        """
        wrapper method for all agent cognition: perceive, retrieve, act, reflect, set goals

        Args:
            game (Game): the current game object

        Returns:
            Union[str, int]: An action string or int flag -999 to trigger skipped action
        """

        # If this is the end of a round, force reflection
        if game.tick == (game.max_ticks_per_round - 1) and self.group != "E":
            reflect(game, self) 
            if self.use_goals:
                self.goals.evaluate_goals(game)
            return -999

        # Percieve the agent's surroundings 
        self.perceive(game)

        # Update this agent's impressions of characters in the same location
        if self.use_impressions:
            self.update_character_impressions(game)

        # act accordingly
        return Act(game, self).act()
