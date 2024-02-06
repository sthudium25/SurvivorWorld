from ..things.items import Item

from collections import defaultdict


class ResourceManager:
    """
    This class handles the global resources of the world.
    It maintains resource quantities and any state changes due to replenishment
    or removal.
    It also allows creation or removal of multiple resources in an easier
    fashion.
    """

    def __init__(self):
        self.resources = defaultdict(list)

    def create_item(self,
                    item_class,
                    name,
                    description,
                    quantity,
                    **properties):
        if not isinstance(item_class, Item):
            print(f'{item_class} must be of things.Item. Creation failed!')
            return False

        # Create instances and store them
        for _ in range(quantity):
            item = item_class(name, description)
            for prop, value in properties.items():
                item.set_property(prop, value)
            self.resources[name] = quantity
        return True

    def remove_item(self, name, n):
        """
        Remove n items from the global resource table.
        Item quantities cannot be negative

        Args:
            name (str): name of item to remove
            n (int): how many items to remove (n >= 0)

        Returns:
            success (bool)
        """
        if n < 0:
            return False
        else:
            count = self.get_item_count(name)
            self.resources[name].update(max(0, count - n))
            return True

    def get_item_count(self, name):
        # Retrieve count of items in the world
        return self.resources[name]
