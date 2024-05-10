"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: setup_agent.py
Description: helper methods for agent setup
"""

import os
import json
from importlib.resources import files, as_file
import random
from typing import Dict, List, Literal
import numpy as np
import openai
from sklearn.metrics.pairwise import cosine_similarity

# relative imports
from ..agent.persona import Persona
from ..managers.scales import TraitScale
from ..gpt import gpt_agent_setup, gpt_helpers
from .general import set_up_openai_client
from . import consts, general
# from . import consts

GPT_RETRIES = 5

def find_similar_character(query, characters, top_n=1):
    # TODO: fill in docstring
    """_summary_

    Args:
        query (_type_): _description_
        characters (_type_): _description_
        top_n (int, optional): _description_. Defaults to 1.

    Returns:
        _type_: _description_
    """

    sim = cosine_similarity(np.array(query).reshape(1, -1),
                            np.array([np.array(v) for v
                                      in characters.values()]))
    idx = sorted(enumerate(sim[0]),
                 key=lambda x: x[1], reverse=True)[:top_n][0][0]
    return idx


def get_or_create_base_facts(description: str, make_new=False, model='gpt-3.5-turbo'):
    # TODO: complete doc string
    """_summary_

    Args:
        description (str): _description_
        make_new (bool, optional): _description_. Defaults to False.
        model (str, optional): _description_. Defaults to 'gpt-3.5-turbo'.

    Returns:
        _type_: _description_
    """
    # If new character is requested, call GPT
    if make_new:
        for i in range(GPT_RETRIES):
            char, error_flag = gpt_agent_setup.get_new_character_from_gpt(description, model) 
            if error_flag:
                print(f"retry {i} for character setup: {description}")
                continue
            else:
                return char
        raise ValueError("GPT failed to create a character with your description. Try something different.")
    # Otherwise compare to premade characters
    else:
        requested_vector = general.get_text_embedding(description)
        try:
            characters = get_character_facts()
        except FileNotFoundError:
            print("No character presets found. Defaulting to new character creation.")
            return gpt_agent_setup.get_new_character_from_gpt(description)

        embedded_characters = {}
        for i, c in enumerate(characters):
            c_vec = general.get_text_embedding(c.__str__())
            embedded_characters[i] = c_vec

        idx = find_similar_character(query=requested_vector,
                                     characters=embedded_characters)
        return characters[idx]


def create_persona(facts: Dict,
                   trait_scores: List = None,
                   archetype=None,
                   model='gpt-3.5-turbo',
                   file_path=None):
    """_summary_

    Args:
        facts (Dict): _description_
        trait_scores (List, optional): _description_. Defaults to None.
        archetype (_type_, optional): _description_. Defaults to None.
        model (str, optional): _description_. Defaults to 'gpt-3.5-turbo'.

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    archetype_game_theory_mapping = {
        "Hubris": "Backstabbing",  # Given their self-centered and assertive traits.
        "Villain": "Backstabbing",  # Villains are typically manipulative and self-serving.
        "Hero": "Cooperation",  # Heroes are often altruistic and collaborative.
        "Student": "Tit-for-Tat",  # Students are learners and may adapt their strategy based on others.
        "Leader": "Cooperation",  # Leaders are usually cooperative, aiming to unite and guide.
        "Damsel in Distress": "Cooperation",  # Likely to seek help and cooperate in situations.
        "Mother": "Cooperation",  # Embodying nurturing and caring traits, inclined to help and cooperate.
        "Warrior": "Backstabbing",  # Focused and combative, might prioritize individual goals over cooperation.
        "Sage Advisor": "Tit-for-Tat",  # Wise and adaptive, responding strategically to the actions of others.
    }

    # If Filepath given, load persona from file.
    if file_path is not None:
        if not os.path.isfile(file_path):  # check that filepath exists
            raise FileNotFoundError(f"No file found at {file_path}")
    
        return Persona.import_persona(file_path)

    # Otherwise, create New Persona
    p = Persona(facts)

    # TODO: Property of Character (Troll, etc.)
    if not trait_scores and not archetype:
        archetype = random.choice(list(archetype_game_theory_mapping.keys()))
    if trait_scores:
        scores = validate_trait_scores(trait_scores)
        monitored_traits = TraitScale.get_monitored_traits()
        for score, named_trait in zip(monitored_traits.items(), scores):
            name, dichotomy = named_trait
            trait = TraitScale(name, dichotomy, score=score)
            # TODO: would be more cost/time effective to ask this to GPT once
            trait.set_adjective(model)
            p.add_trait(trait)
    elif archetype:
        profile = get_archetype_profiles(archetype)
        for scale in profile['traits']:
            low, high, target, name = scale['lowAnchor'], scale['highAnchor'], scale['targetScore'], scale["name"]
            dichotomy = (low, high)

            # Add wiggle/variance to the score (+/- 5%)
            # Personas are only *instantiations* of archetypes, so they can vary
            random_wiggle = np.random.uniform(-5, 5)
            target = target + target * random_wiggle / 100

            trait = TraitScale(name, dichotomy, score=target)
            # TODO: would be more cost/time effective to ask this to GPT once
            trait.set_adjective(model=model)
            p.add_trait(trait)
        p.set_game_theory_strategy(archetype_game_theory_mapping[archetype])  # Sets default strategy based on archetype
        p.set_archetype(archetype)
    else:
        raise ValueError("One of either trait_scores or archetype must be specified.")
    
    return p

def build_agent(agent_description, 
                facts_new, 
                trait_scores: List = None,
                archetype=None,
                model='gpt-3.5-turbo'):
    
    facts = get_or_create_base_facts(agent_description, make_new=facts_new, model=model)
    print(f"Generated facts: {facts}")
    
    missing_keys = validate_facts(facts)
    if len(missing_keys) > 0:
        # get a random backup fact for the category
        # Limited to name, age, occupation
        for k in missing_keys:
            facts[k] = get_backup_fact(k)
    
    p = create_persona(facts, trait_scores, archetype=archetype, model=model)
    return p

    # TODO: How to add affinities? We need the game information to know how many 
    # characters exist in the world. This may need to happen later
    # Maybe once characters are set, there is a start up sequence that sets 
    # all "affinities" in each persona.

def validate_facts(facts_dict):
    required_keys = ['Name', 'Age', 'Occupation']
    if not isinstance(facts_dict, dict):
        print(facts_dict)
        raise TypeError(f"facts must be a dictionary. Got {type(facts_dict)}")
    missing = []
    for k in required_keys:
        if k not in facts_dict:
            print(f"facts is missing {k}")
            missing.append(k)
    return missing

def validate_goals(goals_dict):
    if "flex" not in goals_dict.keys():
        print("No flexible goal set.")
    if "short-term" not in goals_dict.keys():
        # TODO: Modify this goal wording as needed
        goals_dict["short-term"] = "Gain the trust of others. Find allies to prevent yourself\
            from being voted off the island."        
    if "long-term" not in goals_dict.keys():
        # TODO: Modify this goal wording as needed
        goals_dict["long-term"] = "Develop strong alliances. Position yourself to win the game of Survivor."
    return goals_dict


def validate_trait_scores(scores):
    nscores = len(scores)
    # here 9 is currently the number of traits being measured
    # Can always change this to be dynamic.
    if nscores != 9:
        print(f"Only {nscores} provided, filling others randomly")
        rand_scores = np.random.randint(0, 100, size=(9 - nscores))
        scores.extend(rand_scores.tolist())
    scores = np.clip(scores, 0, 100).tolist()
    return scores

def get_archetype_profiles(target: str) -> Dict:
    asset_path = consts.get_assets_path()
    asset_path = os.path.join(asset_path, "archetypes.json")
    with open(asset_path, 'r') as f:
        profiles = json.load(f)

    for atype in profiles['archetypes']:
        if target == atype['name']:
            return atype
    return None

def get_character_facts():
    asset_path = consts.get_assets_path()
    asset_path = os.path.join(asset_path, "character_facts.json")
    with open(asset_path, 'r') as f:
        characters = json.load(f)
    return characters

def get_backup_fact(key):
    asset_path = consts.get_assets_path()
    asset_path = os.path.join(asset_path, "backup_fact_lists.json")
    with open(asset_path, 'r') as f:
        facts = json.load(f)
        print(facts)
    return np.random.choice(facts[key])
