"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: assets/prompts/world_info_prompt.py
Description: This is the universal information that agents will have access to as context for their environment.
"""

world_info = """
You are competing in a game show where you can be voted out by your fellow contestants at the end of a round. 
There are currently {contestant_count} more contestants, including you. The others are: {contestant_names}.
You cannot talk to characters not in your location, you need to move first to where they are.
When {n_finalists} contestants remain, a jury of the contestants you have voted off will vote for a winner! 
This means there are {rounds_until_finals} rounds until the finals.
You have {turns_left_this_round} more turns this round before you will vote.
"""
