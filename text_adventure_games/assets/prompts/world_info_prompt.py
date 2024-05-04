"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: assets/prompts/world_info_prompt.py
Description: This is the universal information that agents will have access to as context for their environment.
"""

# EXPLORATION
world_info = """
You are competing in a game show where your goal is to find a hidden idol somewhere in the island.
You need to search for it in the right location and find it to win.
The first contestant to find the idol wins, so time is of the escence!
The idol is worth 100 points and every aciton you take before finding it substracts 1 point from your total score.
There are currently {contestant_count} more contestants, including you. The others are: {contestant_names_locs}.
You may only talk to characters in your same location. If they are not here, then you need to move first to where their location.
"""
