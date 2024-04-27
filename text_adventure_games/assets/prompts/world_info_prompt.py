"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: assets/prompts/world_info_prompt.py
Description: This is the universal information that agents will have access to as context for their environment.
"""

world_info = """
You are competing in a game show where you can be voted out by your fellow contestants at the end of a round. 
There are currently {contestant_count} more contestants, including you. The others are: {contestant_names_locs}.
You may only talk to characters in your same location. If they are not here, then you need to move first to where their location.
When {n_finalists} contestants remain, a jury of the contestants you have voted off will vote for a winner! 
This means there are {rounds_until_finals} rounds until the finals.
You have {turns_left_this_round} more turns this round before you will vote.
There could be an idol hiding somewhere in the game that grants you immunity from a vote when you have it in your possession. Explore to find it!!
"""
