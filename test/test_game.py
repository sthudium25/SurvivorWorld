import pytest
from text_adventure_games import (
    games, parsing, actions, things, managers, blocks, viz
)


# Initiate the game
class SurvivorWorld(games.Game):
    def __init__(
        self, start_at: things.Location, player: things.Character, characters=None,
        custom_actions=None
    ):
        super().__init__(start_at, player, characters=characters, custom_actions=custom_actions)

    def is_won(self) -> bool:
        """
        Checks whether the game has been won. For this iteration of SurvivorWorld,
        the game is won when the player finds the hidden immunity idol.
        """
        for name, character in self.characters.items():
            if character.get_property("has_idol"):
                msg = "{name} is found the  HIDDEN IMMUNITY IDOL! {name} is safe at tribal council! You WIN!!"
                self.parser.ok(msg.format(name=character.name.title()))
                return True
        return False


@pytest.fixture
def game_fixture():
    # Set up a reusable game state
    # This contains only the camp, cliffs, beach, and ocean
    camp = things.Location(
        "Camp",
        "You are standing in your tribe's base camp."
    )
    cliffs = things.Location(
        "Cliffs",
        """You stand in front of the steep cliffs.
            Climb them carefully so you don't fall.""",
        )
    beach = things.Location(
        "Beach",
        "You stand at the beach, toes in the sand. In front of you is the vast ocean."
    )
    ocean = things.Location(
        "Ocean",
        "You are at the edge of the ocean with waves washing up around your knees.",
    )
    death = things.Location(
        "The Afterlife",
        "You are dead. GAME OVER."
    )
    death.set_property("game_over", True)

    # Add Connections
    camp.add_connection("east", cliffs)
    cliffs.add_connection("climb", beach)
    cliffs.add_connection("jump", death)
    beach.add_connection("south", ocean)
    ocean.add_connection("north", beach)

    # Add some items
    machete = things.Item(
        "machete",
        "a sturdy machete",
        "a sharp machete capable of cutting anything."
    )
    machete.set_property("is_weapon", True)
    machete.set_property("is_fragile", False)
    camp.add_item(machete)

    coconut_shells = things.Item(
        "coconut",
        "halved coconut shells",
        "These shells would be useful for carrying water!"
    )
    coconut_shells.set_property("is_container", True)
    beach.add_item(coconut_shells)

    # Add the well to the camp to test containment
    well = things.Item(
        "well",
        "a well with water in it",
        "The well is made of stone and appears to be deep. It contains cool, refreshing water."
    )
    well.set_property("is_gettable", False)
    well.set_property("is_container", True)
    camp.add_item(well)

    well_water = things.Item(
        "water",
        "water from the well",
        "Cold water. Perfect for a hot day"
    )
    well_water.set_property("is_contained", well)
    camp.add_item(well_water)

    ocean_water = things.Item(
        "the ocean",
        "vast ocean",
        "THERE ARE FISH IN THE OCEAN.",
    )
    ocean_water.set_property("gettable", False)
    ocean_water.set_property("has_fish", True)
    ocean_water.add_command_hint("catch fish")
    ocean_water.add_command_hint("catch fish with basket")
    ocean.add_item(ocean_water)

    # create a Player
    player = things.Character(
        name="The player",
        description="You are an avid fan on the adventure of a lifetime.",
        persona="I am on an adventure. I am charismatic",
    )
    player.set_property("is_hungry", True)

    # Player's torch
    torch = things.Item("torch", "a torch", "Jeff says this is important.")
    torch.set_property("is_lightable", True)
    torch.set_property("is_lit", False)
    torch.add_command_hint("light torch")
    player.add_to_inventory(torch)

    game = SurvivorWorld(camp, player)
    return game


@pytest.fixture
def player(game_fixture):
    return game_fixture.player


def create_item(name, desc, examine):
    item = things.Item(name, desc, examine)
    return item


def test_next_item_id(game_fixture):
    next_id = things.Thing.get_current_id()
    assert next_id == 13


def test_player_items_and_properties(player):
    inv = player.inventory.items
    assert len(inv) == 1
    assert "torch" in inv
    torch = inv["torch"][0]
    assert len(torch.properties) == 3
    assert "is_lightable" in torch.properties
    assert torch.get_property("is_lightable")


def test_item_property_setup(player):
    inv = player.view_inventory()
    print(inv)
    for _, item in inv.items():
        for i in item:
            assert player.is_in_inventory(i.name)


def test_inventory_check(player):
    assert player.inventory.check_inventory("torch")


def test_inventory_item_count(player):
    assert player.inventory.get_quantity("torch") == 1


def test_inventory_get_item(player):
    torch = player.inventory.get_item("torch")
    assert torch
    assert isinstance(torch, things.Item)
    # This should not remove the item from the inventory
    assert player.inventory.get_quantity("torch") == 1


def test_inventory_remove_item(player):
    torch = player.inventory.remove_item("torch")
    assert torch
    assert isinstance(torch, things.Item)
    assert player.inventory.get_quantity("torch") == 0


def test_inventory_get_size(player):
    assert player.inventory.size() == 1
    stick = create_item("stick", "a stick", "a long stick")
    player.add_to_inventory(stick)
    assert player.inventory.size() == 2
    assert player.inventory.get_quantity("stick") == 1
    assert player.is_in_inventory("stick")
    assert not player.is_in_inventory("phone")

