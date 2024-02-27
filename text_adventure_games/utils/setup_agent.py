"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: setup_agent.py
Description: helper methods for agent setup
"""

import os
import re
import json
from typing import Dict, List, Literal
import numpy as np
import openai
from sklearn.metrics.pairwise import cosine_similarity

# relative imports
from ..agent.persona import Persona
from ..scales import affinity, traits
from gpt import gpt_agent as ga


def get_openai_key():
    openai_api = os.getenv("OPENAI_API")
    if not openai_api:
        raise ValueError("You must add an OpenAI API key to your config file.")
    else:
        return openai_api
    

def get_text_embedding(client, text, model="text-embedding-3-small"):
    text_vector = client.embeddings.create(input=[text], model=model).data[0].embedding
    return text_vector


def find_similar_character(query, characters, top_n=1):
    client = openai.Client()
    query_vec = np.array(get_text_embedding(client, query))

    sim = cosine_similarity(query_vec.reshape(1, -1),
                            np.array([np.array(v) for v
                                      in characters.values()]))
    idx = sorted(enumerate(sim[0]),
                 key=lambda x: x[1], reverse=True)[:top_n][0][0]
    return idx


def get_or_create_base_facts(description: str, make_new=False, model='gpt-3.5-turbo'):
    # Create client
    client = openai.Client()

    # If new character is requested, call GPT
    if make_new:
        return ga.get_new_character_from_gpt(client, description, model) 
    # Otherwise compare to premade characters
    else:
        requested_vector = get_text_embedding(client, description)
        try:
            with open("../assets/character_traits.json", 'r') as f:
                characters = json.load(f)
        except FileNotFoundError:
            print("No character presets found. Defaulting to new character creation.")
            return ga.get_new_character_from_gpt(client, description, model)

        embedded_characters = {}
        for i, c in enumerate(characters):
            c_vec = get_text_embedding(client, c.__str__())
            embedded_characters[i] = c_vec

        idx = find_similar_character(query=requested_vector,
                                     characters=embedded_characters)
        return characters[idx]


def create_persona(facts: Dict,
                   goals: Dict,
                   trait_scores: List = None,
                   archetype: Literal["Hubris", "Warrior", "Student"] = None,
                   model='gpt-3.5-turbo'):
    goals = validate_goals(goals)
    p = Persona(facts, goals)

    if trait_scores:
        scores = validate_trait_scores(trait_scores)
        monitored_traits = traits.TraitScale.get_monitored_traits()
        for score, named_trait in zip(monitored_traits.items(), scores):
            name, dichotomy = named_trait
            trait = traits.TraitScale(name, dichotomy, score=score)
            trait.set_adjective(model)
            p.add_trait(trait)
    elif archetype:
        pass
    else:
        raise ValueError("One of trait_scores or archetype must be specified.")


def validate_goals(goals_dict):
    if "flex" not in goals_dict.keys():
        print("No flexible goal set.")
    if "short-term" not in goals_dict.keys():
        goals_dict["short-term"] = "Gain the trust of others. Find allies to prevent yourself from being voted off the island."
    if "long-term" not in goals_dict.keys():
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
