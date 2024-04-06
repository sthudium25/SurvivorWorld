"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: assets/prompts/world_info_prompt.py
Description: This is the universal information that agents will have access to as context for their environment.
"""

world_info = """
Come on in! Welcome to SurvivorWorld! This is a game show in which you can be voted out by 
your fellow contestants at the end of a round. 
There are currently {contestant_count} more contestants, including you. 
When {n_finalists} contestants remain, a jury of the contestants you have voted off will vote for a winner! 
This means there are {rounds_until_finals} rounds until the finals.
You have {turns_left_this_round} more turns this round before you will vote.
Don't get voted out!
"""
