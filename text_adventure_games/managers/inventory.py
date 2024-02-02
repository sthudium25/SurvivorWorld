from ..things.items import Item
from collections import defaultdict, Counter


class Inventory:
    """
    Handles inventory as two dictionaries:
      1. {Item name: [List of Item ids]}
      2. {Item name: quantity}
    Whether it's more efficient to just calculate the quantity every
    time from the list length remains to be seen.
    """
    def __init__(self):
        self.items = defaultdict(list)
        self.item_quantities = Counter()

    def add_item(self, item: Item):
        self.item_quantities[item.name] += 1
        self.items[item.name].append(item.id)

    def remove_item(self, item_name):
        # TODO: should the name or the Item itself be passed here?

        if item_name in self.items and self.items[item_name] > 0:
            self.item_quantities[item_name] -= 1
            # just remove the first one?
            # TODO: how to specify which item to get?
            #   Possible that this will be possible given state
            #   info accessible upon player action
            self.items[item_name].pop()

    def get_quantity(self, item_name):
        return self.item_quantities[item_name]

    def get_inventory_size(self):
        return self.item_quantities.total()

    def view_inventory(self):
        return {i: q for i, q in self.item_quantities.items()}
