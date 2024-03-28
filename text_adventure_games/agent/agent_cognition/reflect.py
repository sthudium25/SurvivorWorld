"""
Author: 

File: agent_cognition/reflect.py
Description: defines how agents reflect upon their past experiences
"""

# Stages of reflection
# 1. self-evaluation of actions: 
#   - what was the quality of your actions?
#   - could your actions have been performed more efficiently and if so why?
# 2. Strategic reflection: relate progress toward goals to the game’s end state
#   - sub-routine that triggers the Goals module for analysis of goals
#       - give previous goal(s)
#       - return Updated or same goals 
# 4. Interpersonal reflection: 
#   - here is how you feel about Person A: <summary of relationship>
#   - Given your experiences of them: <memories>
#   - Would you update your personal understanding and feelings toward Person A?

# What memories should be reflected upon?
# 0. For all types: Just give all memories from the last round + reflection nodes + goals
#   - Would need to store a cache of these in the memory
# 1a. self-eval should focus on the agent's actions 
#   - this means we need to distinguish between self and others' actions
# 2a. strategic reflections should use agent goals and memories relevant to them
#   - 
# 3a. Need just goals from the last round
# 4a. see 4

from typing import TYPE_CHECKING, Dict
import json

# local imports
from text_adventure_games.agent.memory_stream import MemoryType
from text_adventure_games.assets.prompts import reflection_prompts as rp
from text_adventure_games.gpt.gpt_helpers import limit_context_length, gpt_get_action_importance
from text_adventure_games.utils.general import set_up_openai_client

if TYPE_CHECKING:
    from text_adventure_games.games import Game
    from text_adventure_games.things import Character

GPT4_MAX_TOKENS = 8192
REFLECTION_MAX_OUTPUT = 512

def reflect(game: "Game", character: "Character"):
    """
    Perform a complete reflection; this is composed of _ sub-types of reflection:
    1. reflect on actions from past round (inspired by CLIN)
    2. reflect on goals
    3. reflect on relationships

    Args:
        game (Game): _description_
        character (Character): _description_
    """
    generalize(game, character)
    # reflect_on_goals(game, character)
    # reflect_on_relationships(game, character)

def generalize(game, character):
    """
    Reflection upon understanding of the world

    Args:
        game (_type_): _description_
        character (_type_): _description_
    """
    # 1. Get MemoryType.REFLECTION nodes
    # 2. Get nodes from the current round
    # 3. Generalize new observations with old reflections to update/add

    # Get an enumerated list of the REFLECTION nodes for this character
    # MemoryType.REFLECTION == 3
    reflection_ids = character.memory.get_observations_by_type(MemoryType.REFLECTION)
    reflection_desc = character.memory.get_enumerated_description_list(reflection_ids, as_type="str")

    # Get an enumerated list of the action nodes for this character in this round
    this_round_mem_ids = character.memory.get_observations_by_round(game.round)
    this_round_mem_desc = character.memory.get_enumerated_description_list(this_round_mem_ids, as_type="str")

    generalizations = gpt_generalize(game, reflection_desc, this_round_mem_desc)
    print(f"{character.name} generalized: {generalizations}")
    add_generalizations_to_memory(game, character, generalizations)

def reflect_on_goals():
    pass

def reflect_on_relationships():
    pass

def gpt_generalize(game, reflections, new_observations):
    # initialize a client
    client = set_up_openai_client("Helicone")

    # load system prompt
    system_prompt = rp.gpt_generalize_prompt

    # TODO: Potential problem here is what to do if new_observations list exeeds context limit on its own
    # limit_context_length looks through this list backwards, so those could fill up the limit
    # I guess this just means that round max ticks needs to stay small since new_observations is limited to the last round
    user_prompt_items = ["Prior reflections:\n"] + reflections + ["\nNew observations:\n"] + new_observations

    user_prompt_items = limit_context_length(user_prompt_items,
                                             max_tokens=GPT4_MAX_TOKENS-REFLECTION_MAX_OUTPUT,
                                             tokenizer=game.parser.tokenizer)
    user_prompt_str = "".join(user_prompt_items)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt_str},
        ],
        temperature=1,
        top_p=1,
        max_tokens=REFLECTION_MAX_OUTPUT,
        frequency_penalty=0,
        presence_penalty=0
    )
    try:
        out = json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        # TODO: initiate retry logic here
        pass
    else:
        return out

def add_generalizations_to_memory(game: "Game", character: "Character", generalizations: Dict, ):
    """
    Parse the gpt-generated generalizations dict for new reflections
    The structure of this obviously depends on the prompt used.

    Args:
        generalizations (Dict): _description_

    Returns:
        None
    """
    add_new_generalizations(game, character, generalizations)
    update_existing_generalizations(character, generalizations)

def add_new_generalizations(game: "Game", character: "Character", generalizations: Dict):
    """
    Add new generalizations as memories

    Args:
        game (Game): _description_
        character (Character): _description_
        generalizations (Dict): _description_
    """
    try:
        new_gens = generalizations["new"]
    except KeyError:
        # TODO: maybe build in some retry logic?
        pass
    else:
        for ref in new_gens:
            try:
                desc = ref["statment"]
            except KeyError:
                # This is a mal-formed reflection, so skip it
                continue
            else:
                # TODO: should keywords be extracted from reflections?
                ref_kwds = game.parser.extract_keywords(desc)
                ref_importance = gpt_get_action_importance(desc)

                character.memory.add_memory(game.round,
                                            game.tick,
                                            desc,
                                            ref_kwds,
                                            character.location,
                                            success_status=True,
                                            memory_importance=ref_importance,
                                            memory_type=MemoryType.REFLECTION)
                
def update_existing_generalizations(character: "Character", generalizations: Dict):
    """
    Find the appropriate reflection nodes that GPT updated and replace the description

    Args:
        character (Character): _description_
        generalizations (Dict): _description_
    """
    try:
        updated_gens = generalizations["updated"]
    except KeyError:
        # TODO: again, do we want retry logic for reflections if GPT got JSON structure wrong?
        pass
    else:
        for ref in updated_gens:
            try:
                prev_idx = int(ref["index"])
                desc = ref["statement"]
            except (KeyError, ValueError, TypeError):
                # again, this is malformed, so skip
                continue
            else:
                _ = character.memory.update_node_description(node_id=prev_idx, 
                                                             new_description=desc)
                _ = character.memory.update_node_embedding(node_id=prev_idx,
                                                           new_description=desc)
                
                
                
                
