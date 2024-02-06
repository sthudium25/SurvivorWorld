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


def setup_function():
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


def test_next_item_id():
    next_id = things.Thing.get_current_id()
    assert next_id == 13




