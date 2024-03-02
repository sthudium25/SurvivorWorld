"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: gpt_agent.py
Description: Methods that access the OPENAI API and make a call to GPT
"""

import openai

# relative imports
from .. import general

def get_new_character_from_gpt(client, description, model):

    system_prompt = """
You are a character generator. You should fill in the following character information\
based on a short description that will be provided. Create realistic, diverse characters.
Example prompt: A college student from New Mexico
Example Output:
{
  "Name": "Emily Sanchez",
  "Age": 20,
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
    traits_json = general.extract_json_from_string(response.choices[0].message.content)
    return traits_json

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

    client = openai.Client()

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

    client = openai.Client()

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


def get_text_embedding(client, text, model="text-embedding-3-small"):
    text_vector = client.embeddings.create(input=[text], model=model).data[0].embedding
    return text_vector
