from collections import defaultdict
import itertools
import json


class Thing:
    """
    Supertype that will add shared functionality to Items, Locations and
    Characters.
    """

    # Generate an id - ST 1/30/24
    new_id = itertools.count(1)
    _last_id = 0

    def __init__(self, name: str, description: str):
        # TODO: identify things by an id - ST 1/30/24
        self.id = next(Thing.new_id)
        Thing._last_id = self.id

        # A short name for the thing
        self.name = name

        # A description of the thing
        self.description = description

        # A dictionary of properties and their values. Boolean properties for
        # items include: gettable, is_wearable, is_drink, is_food, is_weapon,
        #     is_container, is_surface
        self.properties = defaultdict(bool)

        # A set of special command associated with this item. The key is the
        # command text in invoke the special command. The command should be
        # implemented in the Parser.
        self.commands = set()

    @classmethod
    def get_current_id(cls):
        # Return the next ID that will be assigned
        return cls._last_id + 1

    def to_primitive(self):
        """
        Puts the main fields of this base class into a dictionary
        representation that can safely be converted to JSON
        """
        thing_data = {
            "id": self.id,  # ST - 1/30/24
            "name": self.name,
            "description": self.description,
            "commands": list(self.commands),
            "properties": self.properties,
        }
        return thing_data

    @classmethod
    def from_primitive(cls, data, instance=None):
        """
        Converts a dictionary of values into an instance.
        """
        if not instance:
            instance = cls(data["name"], data["description"])
        for c in data["commands"]:
            instance.add_command_hint(c)
        for k, v in data["properties"].items():
            instance.set_property(k, v)

    def to_json(self):
        data = self.to_primitive()
        data_json = json.dumps(data)
        return data_json

    @classmethod
    def from_json(cls, data_json):
        data = json.loads(data_json)
        instance = cls.from_primitive(data)
        return instance

    def set_property(self, property_name: str, property):
        """
        Sets the property of this item
        """
        self.properties[property_name] = property

    def get_property(self, property_name: str):
        """
        Gets the value of this property for this item (defaults to False)
        """
        return self.properties.get(property_name, None)

    def has_property(self, property_name: str):  # Added by ST - 1/30/24
        """
        Checks if the item has the property
        """
        return property_name in self.properties

    def add_command_hint(self, command: str):
        """
        Adds a special command to this thing
        """
        self.commands.add(command)

    def get_command_hints(self):
        """
        Returns a list of special commands associated with this object
        """
        return self.commands

    def remove_command_hint(self, command: str):
        """
        Returns a list of special commands associated with this object
        """
        return self.commands.discard(command)

    # new methods developed by - ST 1/30/24
    def get_id(self):
        return self.id
