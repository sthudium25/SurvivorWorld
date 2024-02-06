from ..things.items import Item
from collections import defaultdict, Counter


class Inventory:
    """
    Handles inventory as two dictionaries:
      1. {Item name: [List of Item objects]}
      2. {Item name: quantity (int)}
    Whether it's more efficient to just calculate the quantity every
    time from the list length remains to be seen.
    """
    def __init__(self):
        self.items = defaultdict(list)
        self.item_quantities = Counter()

    def add_item(self, item: Item):
        self.item_quantities[item.name] += 1
        self.items[item.name].append(item)

    def get_item(self, item_name, which: int = 1):
        """
        Obtain an Item instance matching by name and index.
        Does not remove the item

        Args:
            item_name (str): item name
            which (int, optional): index of item. Defaults to 1.

        Returns:
            Item: the instance of item_name
        """
        idx = which - 1
        if self.check_inventory(item_name) and self.get_quantity(item_name) > 0:
            print(f"found {item_name} in inventory")
            try:
                return self.items[item_name][idx]
            except IndexError:
                print(f"""There are only {self.get_quantity(item_name)}
                            {item_name}s, not {idx}.""")
                print("Returning the closest one")
                return self.items[item_name][-1]
        else:
            return None

    def remove_item(self, item_name: str, which: int = 1):
        idx = which - 1
        if self.check_inventory(item_name) and self.get_quantity(item_name) > 0:
            print(f"found {item_name} in inventory")
            self.item_quantities[item_name] -= 1
            # just remove the first one?
            # TODO: how to specify which item to get?
            #   Possible that this will be possible given state
            #   info accessible upon player action
            try:
                return self.items[item_name].pop(idx)
            except IndexError:
                print(f"""There are only {self.get_quantity(item_name)}
                            {item_name}s, not {idx}.""")
                print("Returning the closest one")
                return self.items[item_name].pop(-1)
        else:
            return None

    def get_quantity(self, item_name):
        return self.item_quantities[item_name]

    def size(self):
        """
        Get the size of the inventory i.e. sum of all quantities

        Returns:
            int: total items in inventory
        """
        return sum(self.item_quantities.values())

    def view_inventory(self):
        """
        Get a Dict[str: List] representation of the inventory

        Returns:
            dict: the inventory
        """
        return {name: item for name, item in self.items.items()}

    def check_inventory(self, item_name):
        """
        Check by name if an item is in this inventory

        Args:
            item_name (str): the name of the item

        Returns:
            bool: True if found else False
        """
        return item_name in self.items
