from collections import defaultdict
from ..things import Item


class ContainmentManager(object):
    '''
    This class implements a container management system,
    allowing items to possess other items in flexible ways.
    '''
    def __init__(self):
        # This dictionary maps an Item to a list of contained Items
        # These will be tracked by the id of the thing
        self.containment = defaultdict(list)

        # This dictionary keeps track of Items we've seen
        # It will map from the id to the Item object
        self.managed_items = defaultdict(Item)
    
    def manage_new_item(self, item: Item):
        # TODO: is it safe to create this pointer?
        self.managed_items[item.id] = item

    def add_container(self, thing: Item):
        """
        Add a new container to the manager and init with an empty list
        Args:
            thing (Item): an object of class Item
        """
        if thing.id not in self.containment:
            self.containment[thing.id] = []
            self.manage_new_item(thing)

    def add_item(self, container: Item, item: Item):
        # Add an item to the container's list
        if container.id in self.containment:
            self.containment[container.id].append(item.id)
            self.manage_new_item(item)
        else:
            # TODO: Improve missing container handling
            print(f"{container.name} is not a recognized container.")

    def remove_item(self, container: Item, item: Item):
        if container in self.containment and item.id in self.containment[container.id]:
            self.containment[container.id].remove(item.id)
            self.managed_items.remove(item.id)
        else:
            print(f'There is no {item.name} in {container.name}.')

    def get_contents(self, container: Item):
        """
        Retrieves the items within a container

        Args:
            container (Thing): The container whose contents you wish to see

        Returns:
            list: A list of items in the container
        """
        if container in self.containment:
            return self.containment[container]

    def is_contained(self, item: Item):
        # Check if an item is contained in any container
        for container, items in self.containment.items():
            if item.id in items:
                return container
        return False

    def get_managed_item_name(self, item_id: int):
        return self.managed_items[item_id].name

    def get_containment_tree(self):
        for container, items in self.containment.items():
            print(f"{self.get_managed_item_name(container)}:")
            for item in items:
                print(f"      | ---- {self.get_managed_item_name(item)}")
