"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: utils/general.py
Description: helper methods used throughout the project
"""

import os
import re
import json
import string
# from importlib.resources import files, as_file
from typing import Dict

# Relative imports
from . import consts


def extract_target_word(response):
    words = response.split()
    # For debugging purposes check when it fails to return only 1 word.
    if len(words) > 1:
        print("target word list returned is: ", words)
        return words[0].strip(string.punctuation)
    else:
        return words[0].strip(string.punctuation)


def extract_enumerated_list(response):
    # Split the response string into lines
    lines = response.split('\n')

    extracted_words = []
    # Regular expression to match lines with an 
    # enumeration format followed by a single word
    pattern = re.compile(r'^\d+\.\s*(\w+)')

    for line in lines:
        match = pattern.match(line)
        if match:
            extracted_words.append(match.group(1))
    return extracted_words


def extract_json_from_string(s: str):
    # Regular expression to match a JSON structure
    # It looks for an opening curly brace, followed by any character (non-greedily),
    # and then a closing curly brace. The DOTALL flag allows the dot to match newlines.
    pattern = re.compile(r'\{.*?\}', re.DOTALL)
    match = pattern.search(s)
    if match:
        # Extract the JSON string
        json_str = match.group(0)
        try:
            # Attempt to parse the JSON string to ensure it's valid
            json_obj = json.loads(json_str)
            # Return the JSON object if parsing is successful
            return json_obj
        except json.JSONDecodeError:
            # Return None or raise an error if the JSON is invalid
            return None
    return None


def get_archetype_profiles(target: str) -> Dict:
    asset_path = consts.get_assets_path()
    asset_path = os.path.join(asset_path, "persona_profiles.json")
    with open(asset_path, 'r') as f:
        profiles = json.load(f)

    for atype in profiles['archetypes']:
        if target == atype['name']:
            return atype
    return None


def get_character_facts():
    asset_path = consts.get_assets_path()
    asset_path = os.path.join(asset_path, "character_traits.json")
    with open(asset_path, 'r') as f:
        characters = json.load(f)
    return characters
