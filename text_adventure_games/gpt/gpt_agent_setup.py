"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: gpt_agent.py
Description: Methods that access the OPENAI API and make a call to GPT
"""
# TODO: These clients all use personal API KEYS; should confirm what HELICONE can be used for.
import re
import openai

# relative imports
from ..utils import general

def get_new_character_from_gpt(description, model: str = "gpt-3.5-turbo"):

    client = general.set_up_openai_client(org="Penn")

    system_prompt = """
You are a character generator. You should fill in the following character information\
based on a short description that will be provided. Create realistic, diverse characters.
Example prompt: A college student from New Mexico
Example Output:
{
  "Name": "Emily Sanchez",
  "Age": "20",
  "Likes": ["studying, "cinema"],
  "Dislikes": ["procrastination", "fast food"],
  "Occupation": "College Student",
  "Home city": "Albuquerque, New Mexico"

Create a JSON structure from the output.
"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Create a character who fits this description: {description}"
            }
        ],
        temperature=1.25,
        max_tokens=200,
        top_p=1
    )

    facts_json, error_in_json = general.extract_json_from_string(response.choices[0].message.content)
    print(f"Generated JSON: {facts_json}")
    return facts_json, error_in_json

def get_trait_continuum(low: str, high: str, mid: str = None, model='gpt-3.5-turbo'):
    # TODO: Might be able to just set this in the environment and
    # the API handles finding it.
    # api_key = get_openai_key()

    system_prompt = """
    You will be provided two anchor words that represent the extremes on a
    semantic continuum. Consider one end to have a score of 0 and the other
    a score of 100. For example: Evil=0 and Good=100. You may also receive a
    third word which represents the midpoint of the continuum (e.g. neutral=50).
    Your job is to fill in the scale with adjectives.
    """

    user_prompt = ""
    if mid:
        user_prompt += f"Provide a list of 15 adjectives that range from\
        'Low: {low}' to 'Mid: {mid}' to 'High: {high}' with a smooth transition in between."
    else:
        user_prompt += f"Provide a list of 15 adjectives that range from\
        'Low: {low}' to 'High: {high}' with a smooth transition in between."

    client = general.set_up_openai_client(org="Penn")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=1,
        max_tokens=100,
        top_p=0.5)

    continuum = response.choices[0].message.content
    scale = general.extract_enumerated_list(continuum)
    return scale


def get_target_adjective(low: str,
                         high: str,
                         target: int,
                         model='gpt-3.5-turbo',
                         low_int: int = 0,
                         high_int: int = 100):
    # TODO: Might be able to just set this in the environment and
    # the API handles finding it.
    # api_key = get_openai_key()

    system_prompt = f"""
    You will be provided two anchor words that represent the extremes on a
    semantic continuum. Consider one end to have a score of {low_int} and the other a score of {high_int}.
    You will then receive a target number somewhere along the scale.
    You should provide a single adjective that describes the position of the target on the continuum. 
    For example: Evil={low_int} and Good={high_int} and target is 50 --> predict; Neutral.
    """

    user_prompt = f"On a smooth transition scale from {low_int}={low} to {high_int}={high},\
        a target score of {target} is represented by the adjective:"

    client = general.set_up_openai_client(org="Penn")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=1,
        max_tokens=10,
        top_p=0.5)

    target_trait = general.extract_target_word(response.choices[0].message.content)
    return target_trait


def summarize_agent_facts(facts: str, model='gpt-4') -> str:
    """
    Get a short summary of factual information about an agent

    Args:
        facts (Dict): facts about the agent
    """
    dummy_facts = {
        "Name": "Jacob Harrison",
        "Age": 25,
        "Likes": ["coffee brewing", "indie music", "baking", "dogs", "reading"],
        "Dislikes": ["rude customers", "early mornings", "negativity", "instant coffee"],
        "Occupation": "Barista",
        "Home city": "Philadelphia, Pennsylvania"
    }
    system_prompt = "".join(
        ["You will get a dictionary of traits that tell you about a person.",
         "You should write a concise, two-sentence summary of the person and describe their core",
         "characteristics without just listing the person's likes and dislikes.",
         "The facts:\n",
         f"{str(dummy_facts)}\n",
         "are summarized as:\n",
         "Jacob Harrison is a 25-year-old barista from Philadelphia who has a passion for",
         "creating delicious coffee blends and treats. He finds solace in indie music and", 
         "enjoys spending his free time baking and getting lost in the pages of a good book.",
         "Jacob is a compassionate individual who values positivity and dislikes rude behavior or early mornings. ",
         "His love for dogs adds a playful and nurturing aspect to his personality, ",
         "creating a warm and inviting presence in both his professional and personal life."])
    
    client = general.set_up_openai_client(org="Penn")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": facts
            }   
        ],
        stop=".",
        max_tokens=100,
        presence_penalty=0.2,
        temperature=1
    )
    summary = response.choices[0].message.content.lower()
    summary = re.sub("summary:?", "", summary)
    return summary
