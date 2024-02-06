from .base import Thing
from .items import Item
# from .locations import Location
from ..managers.inventory import Inventory


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
    * An inventory of items that they are carrying - instance of Inventory
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

        # ST - change 2/5/24
        self.inventory = Inventory()
        self.location = None

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

    def is_in_inventory(self, item: Item):
        """
        Checks if a character has the item in their inventory
        """
        return self.inventory.check_inventory(item.name)

    def remove_from_inventory(self, item: Item):
        """
        Removes an item to a character's inventory.
        """
        item.owner = None
        self.inventory.get_item(item.name)
