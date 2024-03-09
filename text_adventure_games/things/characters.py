from .base import Thing
from .items import Item
# from .locations import Location
from ..managers.inventory import Inventory
from ..agent.persona import Persona
from ..gpt.gpt_agent_cognition import AgentKani


class Character(Thing):
    """
    This class represents the player and non-player characters (NPC).
    Characters have:
    * A name (cab be general like "gravedigger")
    * A description ('You might want to talk to the gravedigger, specially if
      your looking for a friend, he might be odd but you will find a friend in
      him.')
    * A persona; Managed as a class containing personall traits and affinities
        to other characters.
    * A location (the place in the game where they currently are)
    * An inventory of items that they are carrying - instance of Inventory
    * TODO: A dictionary of items that they are currently wearing
    * TODO: A dictionary of items that they are currently weilding
    """

    def __init__(
        self, name: str, description: str
    ):
        super().__init__(name, description)
        # TODO: what to do with the character properties???
        self.set_property("character_type", "notset")
        self.set_property("is_dead", False)

        # ST - change 2/5/24
        self.inventory = Inventory()
        self.location = None
        self.alliance = []

    def to_primitive(self):
        """
        Converts this object into a dictionary of values the can be safely
        serialized to JSON.

        Notice that object instances are replaced with their name. This
        prevents circular references that interfere with recursive
        serialization.
        """
        thing_data = super().to_primitive()

        # TODO: how do we handle this now that Persona is a class?
        thing_data['persona'] = self.persona

        inventory = {}
        for k, v in self.inventory.view_inventory():
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

    def add_to_inventory(self, item: Item):
        """
        Locations hold item instances, so we can access all that info.
        Add an item to the character's inventory.
        """
        if item.location is not None:
            item.location.remove_item(item)
            item.location = None
        self.inventory.add_item(item)
        item.owner = self

    def is_in_inventory(self, item_name):
        """
        Checks if a character has the item in their inventory
        """
        return self.inventory.check_inventory(item_name)

    def remove_from_inventory(self, item: Item):
        """
        Removes an item to a character's inventory.
        """
        item.owner = None
        self.inventory.get_item(item.name)

    def view_inventory(self):
        """
        View the items in an inventory

        Returns:
            dict: items present in the inventory
        """
        return self.inventory.view_inventory()
    
    def update_character_affinity(character):
        """
        Update the probability that this character works/agrees with someone else.
        """
        pass

    def get_alliance_summary(self):
        alliance_summary = ""
        alliance_summary += f"You are allied with {' '.join([char.name for char in self.alliance])}."
        return alliance_summary


class GenerativeAgent(Character):
    
    def __init__(self, persona: Persona):
        super().__init__(persona.facts["name"], persona.summary)
        # TODO: memory stream currently in persona but may be hard to access
        self.persona = persona
        self.persona.initialize_memory(self.id)

        # Custom Kani class here? which could store this character's bio as "always_included"
        # Route from this Kani to Reflect, Act, Perceive Kanis?
        self.agent_ai = AgentKani(persona) # I don't really want to store the persona in two places

    def get_character_summary(self):
        """
        Get a summary of the traits for this agent

        Returns:
            str: a standard summary paragraph for this agent
        """
        persona_summary = self.persona.get_personal_summary()
        alliance_summary = self.get_alliance_summary()
        return persona_summary + ' ' + alliance_summary

    def engage(self, round, tick, vote):
        if vote:
            # At end of round: agent votes and reflects
            self.agent_ai.vote()
            self.agent_ai.reflect()
        elif tick == 0:
            # At start of round: agent plans
            self.agent_ai.plan()
        
        self.agent_ai.act()
 
    # def reflect(self):
    #     # Look back at observations from this round
    #     pass

    # def perceive(self):
    #     # Collect the latest information about the location
    #     pass

    # def act(self):
    #     # Intent determination here?
    #     pass

    

    
