
vote_system_ending = """
You are currently at tribal council so you must vote for another tribe member. 
Use the provided information about your position in the game, goals, relationships, 
and memories to cast a vote that you believe will improve your position in the game. 
Weight or interpret the memories based on their influence of the voting decision you need to make.
This could be sticking with an alliance or being deceitful, the choice is up to you. 
Simply respond with the name of the contestant you are voting for.
"""

vote_user_prompt = """
You are in a voting round of the game, so you must select another contestant to vote off the tribe. 
This person will be out of the game for good, but they may be able to cast a vote to help
determine the final winner of the game.

Given your knowledge of the game, yourself, and the other players, select one of the following
players to vote for:
{vote_options}

Who will you vote for? Return their name. My vote is: 
"""
