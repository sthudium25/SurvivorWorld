"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: utils/general.py
Description: helper methods used throughout the project
"""

from collections import defaultdict
import os
import re
import json
import string
import numpy as np
# from importlib.resources import files, as_file
from typing import Dict
from openai import OpenAI
from kani.engines.openai import OpenAIEngine

# local imports
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

def get_logger_extras(game, character):
    extras = {}
    extras["character_name"] = character.name
    extras["character_id"] = character.id
    extras["character_group"] = character.group
    extras["round"] = game.round
    extras["tick"] = game.tick
    extras["total_ticks"] = game.total_ticks
    extras["experiment_name"] = game.experiment_name
    extras["experiment_id"] = game.experiment_id
    return extras

def normalize_name(name):
    common_prefixes = ["mr", "ms", "mrs", "dr", "sir", "lady", "captain", "prof", "professor"]
    common_suffixes = ["jr", "sr", "ii", "iii", "iv", "phd", "md"]
    # Convert to lowercase
    name = name.lower()
    # Remove non-alphanumeric characters
    name = ''.join(e for e in name if e.isalnum() or e.isspace())
    
    # Split the name to handle prefixes and suffixes more effectively
    name_parts = name.split()
    
    # Remove prefixes and suffixes
    if name_parts:
        if name_parts[0] in common_prefixes:
            name_parts = name_parts[1:]  # Remove the first element (prefix)
        if name_parts and name_parts[-1] in common_suffixes:
            name_parts = name_parts[:-1]  # Remove the last element (suffix)
    
    # Rejoin the name parts
    normalized_name = " ".join(name_parts)
    
    return normalized_name

def extract_target_word(response):
    words = response.split()
    # For debugging purposes check when it fails to return only 1 word.
    if len(words) > 1:
        # print("target word list returned is: ", words)
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
    # print(f"Pre-JSON extraction string from GPT: {s}")
    # Regular expression to match a JSON structure
    # It looks for an opening curly brace, followed by any character (non-greedily),
    # and then a closing curly brace. The DOTALL flag allows the dot to match newlines.
    pattern = re.compile(r'\{.*?\}', re.DOTALL)
    match = pattern.findall(s)
    if match:
        # Extract the JSON string
        json_str = match[0]
        json_str, flag = try_fix_json(json_str)
        return json_str, flag
    return None

def try_fix_json(json_str):
    try:
        return json.loads(json_str), False
    except json.JSONDecodeError as e:
        err_msg = str(e)
        if "Expecting value" in err_msg:
            before_error = json_str[:e.pos]
            after_error = json_str[e.pos:]

            # Attempt to insert a missing quotation mark
            fixed_json_str = before_error + '"' + after_error

            # Recursively try to fix
            return try_fix_json(fixed_json_str)
    return json_str, True

def parse_json_garbage(s):
    s = s[next(idx for idx, c in enumerate(s) if c in "{["):]
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        return json.loads(s[:e.pos])

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
                    new_observations[desc_type] = [f'No {desc_type}']
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
                    diff[key] = [description2]
            else:
                # If the key doesn't exist in the first dictionary, add it to the difference
                diff[key] = [value2]
    return diff

def enumerate_dict_options(options, names_only=False, inverted=False):
    """
    Used by GPT-pick an option. Expects keys are descriptions and
    values are the name of the corresponding option.

    Args:
        options (dict): Dict[description of option, option_name]

    Returns:
        _type_: _description_
    """
    options_list = list(options.keys())
    choices_str = ""
    # Create a numbered list of options
    if names_only:
        # for cases where the dict is of the form name:object
        if inverted:
            for i, name in enumerate(options.keys()):
                choices_str += "{i}. {n}\n".format(i=i, n=name)
            return choices_str, None
        else:
            for i, name in enumerate(options.values()):
                choices_str += "{i}. {n}\n".format(i=i, n=name)
            return choices_str, None
        # for cases where the dict is of the form name:object
        if inverted:
            for i, name in enumerate(options.keys()):
                choices_str += "{i}. {n}\n".format(i=i, n=name)
            return choices_str, None
        else:
            for i, name in enumerate(options.values()):
                choices_str += "{i}. {n}\n".format(i=i, n=name)
            return choices_str, None
    else:
        for i, (k, v) in enumerate(options.items()):
            choices_str += "{i}. {v}: {k}\n".format(i=i, v=v, k=k)
        return choices_str, options_list

def combine_dicts_helper(existing, new):
    for k, v in new.items():
        if k in existing:
            existing[k].extend(v)
        else:
            existing[k] = v
    return existing

def get_text_embedding(text, model="text-embedding-3-small", *args):
    """
    Calls the OpenAI embeddings api

    Args:
        text (str): text to embed
        model (str, optional): the embedding model to use. Defaults to "text-embedding-3-small".

    Returns:
        np.array (1, 1536): array of embeddings 
    """
    if not text:
        return None
    client = set_up_openai_client(org="Penn")
    text_vector = client.embeddings.create(input=[text], model=model, *args).data[0].embedding
    return np.array(text_vector)

def create_dirs(fp):
    os.makedirs(os.path.dirname(fp), exist_ok=True)

def write_to_json(fp, data: dict):
    if os.path.isfile(fp) and os.path.getsize(fp) > 0:
        with open(fp, "r+") as f:
            # Load existing data into a dictionary
            existing_data = json.load(f)
            # Update dictionary with new data
            existing_data.update(data)
            # Write back to file
            f.seek(0)  # Reset file position to the beginning.
            json.dump(existing_data, f, indent=4)
            f.truncate()  # Remove remaining part of old data
    else:
        # Create new file and write data
        with open(fp, "w") as f:
            json.dump(data, f, indent=4)
