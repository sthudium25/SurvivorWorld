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
from typing import Dict, Literal
from openai import OpenAI
from kani.engines.openai import OpenAIEngine

# Relative imports
from . import consts


def set_up_openai_client(org="Penn", **kwargs):
    key = consts.get_openai_api_key(org)
    params = kwargs.copy()
    params.update({"api_key": key})
    if org == "Helicone":
        base_url = consts.get_helicone_base_path()
        params.update({"base_url": base_url})
    client = OpenAI(**params)
    return client

def set_up_kani_engine(org="Penn", model='gpt-4', **kwargs):
    key = consts.get_openai_api_key(org)
    engine = OpenAIEngine(key, model=model, **kwargs)
    return engine


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


def parse_location_description(text):
    by_description_type = re.split('\n+', text)
    new_observations = {}
    if len(by_description_type) >= 1:
        desc_type, loc = map(lambda x: x.strip(), by_description_type[0].split(":"))
        new_observations[desc_type] = [loc]
        for description in by_description_type[1:]:
            if description:
                try: 
                    desc_type, player, observed = map(lambda x: x.strip(), description.split(":"))
                except ValueError:
                    # Likely not enough values to unpack
                    desc_type = description.split(":")[0]
                    new_observations[desc_type] = [f'No {desc_type} here']
                    continue
                if "(" in observed:
                    new_observations[desc_type] = [f"{player} {obs}" for obs in observed.split(';') if obs]
                else:
                    new_observations[desc_type] = [f"{player} {obs}" for obs in observed.split(',') if obs]
    return new_observations


def find_difference_in_dict_lists(dict1, dict2):
    if dict1 is None:
        if dict2 is None:
            raise TypeError(f"{type(dict2)} is not comparable.")
        else:
            return dict2

    diff = {}
    # Iterate through each key and value in the second dictionary
    for key, value2 in dict2.items():
        for description2 in value2:
            # Check if the key exists in the first dictionary
            if key in dict1:
                # If the key exists, compare the lists
                # value1 = dict1[key]
                if any([description2 == desc1 for desc1 in dict1[key]]):
                    continue
                    # If the value was not matched by anything in dict1[key]
                else:
                    diff[key] = description2
            else:
                # If the key doesn't exist in the first dictionary, add it to the difference
                diff[key] = value2
    return diff
