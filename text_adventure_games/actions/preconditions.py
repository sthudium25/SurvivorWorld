from ..things import Thing  # , Location


# def at(
#     thing: Thing, location: Location, describe_error: bool = True
# ) -> bool:
#     """
#     Checks if the thing is at the location.
#     """
#     # The character must be at the location
#     if not thing.location == location:
#         message = "{name} is not at {loc}".format(
#             name=thing.name.capitalize(), loc=location.name
#         )
#         if describe_error:
#             describe_failed_command(message, game)
#         return False
#     else:
#         return True


# def has_connection(
#     location: Location, direction: str, describe_error: bool = True
# ) -> bool:
#     """
#     Checks if the location has an exit in this direction.
#     """
#     if direction not in location.connections:  # JD logical change
#         m = "{location_name} does not have an exit '{direction}'"
#         message = m.format(
#             location_name=location.name.capitalize(), direction=direction
#         )
#         if describe_error:
#             describe_failed_command(message, game)
#         return False
#     else:
#         return True


# def is_blocked(
#     location: Location, direction: str, describe_error: bool = True
# ) -> bool:
#     """
#     Checks if the location blocked in this direction.
#     """
#     if location.is_blocked(direction):
#         message = location.get_block_description(direction)
#         if describe_error:
#             describe_failed_command(message, game)
#         return True
#     else:
#         return False


# def property_equals(
#     thing: Thing, property_name: str, property_value: str,
#     error_message: str = None, display_message_upon: bool = False,
#     describe_error: bool = True,
# ) -> bool:
#     """
#     Checks whether the thing has the specified property.
#     """
#     if thing.get_property(property_name) != property_value:
#         if display_message_upon is False:
#             if not error_message
#                 e = "{name}'s {property_name} is not {value}":
#                 error_message = e.format(
#                     name=thing.name.capitalize(),
#                     property_name=property_name,
#                     value=property_value,
#                 )
#             if describe_error:
#                 describe_failed_command(error_message, game)
#         return False
#     else:
#         if display_message_upon is True:
#             if not error_message:
#                 error_message = "{name}'s {property_name} is {value}".format(
#                     name=thing.name.capitalize(),
#                     property_name=property_name,
#                     value=property_value,
#                 )
#             if describe_error:
#                 describe_failed_command(error_message, game)
#         return True


# def has_property(
#     thing: Thing, property_name: str, error_message: str = None,
#     display_message_upon: bool = False, describe_error: bool = True,
# ) -> bool:
#     """
#     Checks whether the thing has the specified property.
#     """
#     if not thing.get_property(property_name):
#         if display_message_upon is False:
#             if not error_message:
#                 error_message = "{name} {property_name} is False".format(
#                     name=thing.name.capitalize(), property_name=property_name
#                 )
#             if describe_error:
#                 describe_failed_command(error_message, game)
#         return False
#     else:
#         if display_message_upon is True:
#             if not error_message:
#                 error_message = "{name} {property_name} is True".format(
#                     name=thing.name.capitalize(), property_name=property_name
#                 )
#             if describe_error:
#                 describe_failed_command(error_message, game)
#         return True


# def loc_has_item(
#     location: Location, item: Item, describe_error: bool = True
# ) -> bool:
#     """
#     Checks to see if the location has the item.  Similar funcality to at, but
#     checks for items that have multiple locations like doors.
#     CCB - todo - update this if we refactor to include a Connection item.
#     """
#     if item.name in location.items:
#         return True
#     else:
#         message = "{loc} does not have {item}".format(
#             loc=location.name, item=item.name
#         )
#         if describe_error:
#             describe_failed_command(message, game)
#         return False


# def is_in_inventory(
#     character: Character, item: Item, describe_error: bool = True
# ) -> bool:
#     """
#     Checks if the character has this item in their inventory.
#     """
#     if not character.is_in_inventory(item):
#         message = "{name} does not have {item_name}".format(
#             name=character.name.capitalize(), item_name=item.name
#         )
#         if describe_error:
#             describe_failed_command(message, game)
#         return False
#     else:
#         return True


def was_matched(
    thing: Thing, error_message: str = None, describe_error: bool = True
) -> bool:
    """
    Checks to see if the thing was matched by the parser.
    """
    if thing is None:
        # if not error_message:
        #     message = "{thing_type} was not matched by the parser.".format(
        #         thing_type=thing.name.capitalize()  # JD logical change
        #     )
        # if describe_error:
        #     describe_failed_command(message, game)
        return False
    else:
        return True
