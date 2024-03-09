"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/cognition/reflect.py
Description: Defines agent reflection upon recent events. 
This is triggered at the end of a round in the game, but reflection could potentially further than 1 round.
At the moment, these are simply a set of methods, not a class.
It defines how an agent makes a reflection and returns this as a new observation
"""

from typing import List


def get_observations_from_round(stream, round, n=None):
    try:
        last_round_nodes = stream.observations[round]
    except KeyError:
        print(f"No observations found from round {round}. Reflecting on last known observations.")
        last_round_nodes = stream.observations[max(stream.observations)]
    if n and len(last_round_nodes) > n:
        last_round_nodes = last_round_nodes[-stream.reflection_distance:]
    return last_round_nodes

def build_observations_list(stream, round, n=None):
    last_round_nodes = get_observations_from_round(stream, round, n)
    enumerated_obs = [f"{i}. {node.node_context}\n" for i, node in enumerate(last_round_nodes)]
    return enumerated_obs

def reflect(stream, round, n=None):
    observations_list = build_observations_list(stream, round, n)


def get_top_reflection_questions(character, observations: List[str], model="gpt-3.5-turbo"):
    # api_key = get_openai_api_key()
    # engine = OpenAIEngine(api_key, model=model)
    system_prompt = """You are a contestant on the gameshow Survivor. 
    Given an enumerated list of observations you saw in the last round, 
    extract 3 key questions that need additional consideration. 
    These questions should be based on the content of the observations and 
    prioritize questions that cannot be answered by the current observations."""
