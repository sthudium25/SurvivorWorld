from .base import Thing
from .items import Item
from .locations import Location
from ..gpt.agent_kani import AgentKani


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
    
    def __init__(self, name: str, description: str, persona: str):
        super().__init__(name, description, persona)
        # super().__init__(persona.facts["name"], persona.summary, persona="see subclass")
        # TODO: memory stream currently in persona but may be hard to access
        # self.persona = persona
        # self.persona.initialize_memory(self.id)

        # Custom Kani class here? which could store this character's bio as "always_included"
        # Route from this Kani to Reflect, Act, Perceive Kanis?
        # self.agent_ai = AgentKani(persona, name)  # I don't really want to store the persona in two places

    def get_character_summary(self):
        """
        Get a summary of the traits for this agent

        Returns:
            str: a standard summary paragraph for this agent
        """
        persona_summary = self.persona.get_personal_summary()
        alliance_summary = self.get_alliance_summary()
        return persona_summary + ' ' + alliance_summary

    def engage(self, game, round, tick, 
               # vote
               ):
        location_description = self.perceive(game)
        print(f"{self.name} memories:")
        print(self.get_memories())
        # if vote:
        #     # At end of round: agent votes and reflects
        #     self.agent_ai.vote()
        #     self.agent_ai.reflect()
        # elif tick == 0:
        #     # At start of round: agent plans
        #     self.agent_ai.plan()
        return input("\n>")
        #self.agent_ai.full_round("Select an action to take.")
        # need to access the game history if this player is in the same as the last one
        # need to describe a new setting if this player is in a different location
 
    def perceive(self, game):
        # Collect the latest information about the location
        location_description = game.describe()
        self.memory.append({"role": "user", "content": location_description})
        print(f"{self.name} has {len(self.memory)} memories.")
        # It would be helpful to get lists of 
        # * Item names, Character names, and the location
        # These could be passed to Kani to help retrieve the relevant ObservationNodes
        return location_description

    def get_memories(self):
        return [m['content'] for m in self.memory]

    # def reflect(self):
    #     # Look back at observations from this round
    #     pass

    

    # def act(self):
    #     # Intent determination here?
    #     pass
