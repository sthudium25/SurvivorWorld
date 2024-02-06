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
        self.item_quantities[item] += 1
        self.items[item.name].append(item)

    def get_item(self, item_name, which: int = 1):
        item_idx = which - 1
        requested_item = self._remove_item(item_name, item_idx)
        return requested_item

    def _remove_item(self, item_name: str, idx: int):
        # TODO: should the name or the Item itself be passed here?
        n = self.item_quantities[item_name]

        if item_name in self.items and n > 0:
            self.item_quantities[item_name] -= 1
            # just remove the first one?
            # TODO: how to specify which item to get?
            #   Possible that this will be possible given state
            #   info accessible upon player action
            try:
                return self.items[item_name].pop(idx)
            except IndexError:
                print(f"There are only {n} {item_name}s, not {idx}.")
                print("Returning the closest one")
                return self.items[item_name].pop(-1)
        else:
            return None

    def get_quantity(self, item_name):
        return self.item_quantities[item_name]

    def get_inventory_size(self):
        return self.item_quantities.total()

    def view_inventory(self):
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
