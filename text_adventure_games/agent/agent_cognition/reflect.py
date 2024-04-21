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
from text_adventure_games.gpt.gpt_helpers import limit_context_length, gpt_get_action_importance, get_prompt_token_count, GptCallHandler
from text_adventure_games.utils.general import set_up_openai_client
from ordered_set import OrderedSet
from . import retrieve

if TYPE_CHECKING:
    from text_adventure_games.games import Game
    from text_adventure_games.things import Character

GPT4_MAX_TOKENS = 8192
REFLECTION_MAX_OUTPUT = 512
REFLECTION_RETRIES = 5

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


# def generalize(game, character):
#     """
#     Reflection upon understanding of the world

#     Args:
#         game (_type_): _description_
#         character (_type_): _description_
#     """
#     # 1. Get MemoryType.REFLECTION nodes
#     # 2. Get nodes from the current round
#     # 3. Generalize new observations with old reflections to update/add

#     # Get an enumerated list of the action nodes for this character in this round
#     this_round_mem_ids = character.memory.get_observations_by_round(game.round)
#     this_round_mem_desc = character.memory.get_enumerated_description_list(this_round_mem_ids, as_type="str")

#     gpt_generalize(game, character, this_round_mem_desc)


def generalize(game, character):
    """
    This function adds/updates reflections to/in the character's memory, based on their impressions
    of the remaining agents and previous reflections, as well as observations from the current round:
     
    1. Get MemoryType.REFLECTION nodes
    2. Get nodes from the current round
    3. Generalize new observations with old reflections to update/add

    Args:
        game (_type_): _description_
        character (_type_): _description_
    """

    # make a dictionary with the desired GPT parameters
    model_params = {
            "api_key_org": "Helicone",
            "model": "gpt-4",
            "max_tokens": REFLECTION_MAX_OUTPUT,
            "temperature": 1,
            "top_p": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "max_retries": 5
            }
    
    # how many memories to get during retrieval, which is called 4 times (once per passed question)
    memories_per_retrieval = 10
 
    # initialize a client
    client = set_up_openai_client("Helicone")

    ### Get Static Components (System Prompt and Impressions don't update during Reflection) ###

    # load system prompt
    system_prompt = character.get_standard_info(game, include_goals=False, include_perceptions=False) + '\n\n' + rp.gpt_generalize_prompt
    # get the number of tokens in the system prompt
    system_prompt_token_count = get_prompt_token_count(content=system_prompt, role='system', pad_reply=False)
    
    # Get IMPRESSIONS of each character still in the game
    impressions = [character.impressions.get_multiple_impressions(game.characters.values())]

    # count the number of tokens in the impressions, including a padding for GPT's reply
    # containing <|start|>assistant<|message|>
    impressions_token_count = get_prompt_token_count(content=impressions, role='user', pad_reply=True)

    # make a list of relevant memories that have been retrieved based on the query questions
    relevant_memories = []
    for question in rp.memory_query_questions:
        for memory in retrieve.retrieve(game=game, character=character, query=question, n=memories_per_retrieval, include_idx=True):
            relevant_memories += memory
    relevant_memories = set(relevant_memories)
    # include a newline appended to the end of each memory string
    relevant_memories = [memory+'\n' for memory in relevant_memories]

    # get the relevant memories token count (role=None and pad_reply=False because we've already accounted for these)
    relevant_memories_token_count = get_prompt_token_count(content=relevant_memories, role=None, pad_reply=False)

    # get the relevant memories primer messsage token count
    relevant_memories_primer = ['Relevant Memories:\n']
    rel_mem_primer_token_count = get_prompt_token_count(content=relevant_memories_primer, role=None, pad_reply=False)

    # the instructions telling GPT to generate high-level insights
    insight_q_prompt = ['\n'+rp.insight_question]
    # get the insight prompt token count
    insight_q_token_count = get_prompt_token_count(content=insight_q_prompt, role=None, pad_reply=False)

    # while there are still relevant memories that haven't been reflected on
    # (note that we remove them from new_observations after reflecting on them)
    while relevant_memories_token_count > 0:

        # limit the user prompt items to fit in GPT's context size
        # (keep_most_recent=False allows us to keep ealier/older observations)
        relevant_memories_limited = limit_context_length(relevant_memories,
                                                 max_tokens=GPT4_MAX_TOKENS - # GPT's context limit
                                                            REFLECTION_MAX_OUTPUT - # GPT's response limit
                                                            system_prompt_token_count - # system message tokens
                                                            impressions_token_count - # impressions tokens
                                                            rel_mem_primer_token_count - # relevant memories primer tokens
                                                            insight_q_token_count, # insight message tokens
                                                 tokenizer=game.parser.tokenizer,
                                                 keep_most_recent=False)
        
        # get user input consisting of impressions, relevant memories (with primer), and the insight instructions
        user_prompt_list = impressions + relevant_memories_primer + relevant_memories_limited + insight_q_prompt
        
        # join the list items into a string – note that the list values end with newline characters,
        # so join using an empty string
        user_prompt_str = "".join(user_prompt_list)

        print('-'*50)
        print(f"{character.name} reflects on the following memories:", user_prompt_str)
        print('-'*50)

        # get GPT's response
        response = GptCallHandler(**model_params).generate(
            system=system_prompt,
            user=user_prompt_str
        )

        # convert string response to dictionary
        new_generalizations = json.loads(response.choices[0].message.content)
        print(f"{character.name} generalized: {new_generalizations}")

        # add the new generalizations to the character's memory
        add_generalizations_to_memory(game, character, new_generalizations)

        # reset relevant memories to exclude all from the previous reflection
        # (this also removes the relevant memories primer string)
        relevant_memories = list(OrderedSet(relevant_memories) - OrderedSet(relevant_memories_limited))
        # get the updated new observations token count
        relevant_memories_token_count = get_prompt_token_count(content=relevant_memories, role=None, pad_reply=False)


def add_generalizations_to_memory(game: "Game", character: "Character", generalizations: Dict, ):
    """
    Parse the gpt-generated generalizations dict for new reflections.
    The structure of this obviously depends on the prompt used.

    Args:
        generalizations (Dict): _description_

    Returns:
        None
    """
    # print(f"Adding {character.name}'s generalizations to memory")
    add_new_generalizations(game, character, generalizations)
    update_existing_generalizations(character, generalizations)


def add_new_generalization_helper(game: "Game", character: "Character", generalization: Dict):
    try:
        desc = generalization["statement"]
    except KeyError:
        # This is a mal-formed reflection, so skip it
        pass
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
                                    memory_type=MemoryType.REFLECTION.value,
                                    actor_id=character.id)


def add_new_generalizations(game: "Game", character: "Character", generalizations: Dict):
    """
    Add new generalizations as memories.

    Args:
        game (Game): _description_
        character (Character): _description_
        generalizations (Dict): _description_
    """
    try:
        new_gens = generalizations["new"]
    except (KeyError, TypeError):
        # TODO: maybe build in some retry logic?
        pass
    else:
        for ref in new_gens:
            add_new_generalization_helper(game=game,
                                          character=character,
                                          generalization=ref)
                

def update_existing_generalizations(game: "Game", character: "Character", generalizations: Dict):
    """
    Find the appropriate reflection nodes that GPT updated and replace the description

    Args:
        character (Character): _description_
        generalizations (Dict): _description_
    """
    try:
        updated_gens = generalizations["updated"]
    except (KeyError, TypeError):
        # TODO: again, do we want retry logic for reflections if GPT got JSON structure wrong?
        pass
    else:
        for ref in updated_gens:
            memory_type = character.get_observation_type(ref['index'])
            print(f"{character.name} tried to update the following memory type: {memory_type}.")

            if memory_type != MemoryType.REFLECTION:
                add_new_generalization_helper(game=game, character=character, generalization=ref)
            
            else:
                print(f"Updating generalization: {ref} for {character.name}")
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
                
    
                












    # ### Get the New Observations ###

    # # Get an enumerated list of the action nodes for this character in the current round
    # this_round_mem_ids = character.memory.get_observations_by_round(game.round)
    # new_observations = character.memory.get_enumerated_description_list(this_round_mem_ids, as_type="str")

    # # get the new observations token count
    # new_observations_token_count = get_prompt_token_count(content=new_observations, role=None, pad_reply=False)