"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent_cognition/act.py
Description: defines how agents select an action given their perceptions and memory
"""

# Steps to choosing an action:
# 1. perceive environment (percieve) -- already put into memory
# 2. collect goals, world info, character relationships (retreive)
# 3. get a list of the currently available actions (game.actions)
# 4. Ask GPT to pick an option 
# 5. Parse and return


# local imports
from text_adventure_games.gpt.gpt_helpers import limit_context_length
from text_adventure_games.utils.general import set_up_openai_client, enumerate_dict_options
from .retrieve import retrieve

GPT4_MAX_TOKENS = 8192
ACTION_MAX_OUTPUT = 100
ACTION_RETRIES = 5


def act(game, character):
    available_actions = game.parser.actions

    system_prompt = build_system_message(game, character, available_actions)

    user_prompt = build_user_message(game, character)

    action_to_take = generate_action(system_prompt, user_prompt)
    game.logger.debug(f"{character.name} chose to take action: {action_to_take}")
    print(f"{character.name} chose to take action: {action_to_take}")
    return action_to_take

def generate_action(system_prompt, user_prompt):
    client = set_up_openai_client("Helicone")

    for i in range(ACTION_RETRIES):
        # print(f"retry {i}/{ACTION_RETRIES} for this character")
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=1,
                top_p=1,
                max_tokens=ACTION_MAX_OUTPUT,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            out = response.choices[0].message.content
        except Exception as e:
            continue
        else:
            return out
    return None

def build_system_message(game, character, game_actions) -> str:
    system = collect_system_info(game, character)
    choices_str, _ = enumerate_dict_options(game_actions, names_only=True)
    
    system += "".join([
        "Using the information provided, generate a short action statement in the present tense from your perspective. ",
        "Be sure to mention any characters you wish to interact with by name. ",
        # "If you want to take a series of actions, separate each atomic action with a comma. ",
        # "Otherwise, do not include commas in your action statement. ",
        "Examples could be:\n",
        "Go outside to the garden.\n",
        "Talk to Tom about strategy\n",
        "Pick up the stone from the ground\n",
        "Give your food to the guard\n",
        "Climb up the tree\n\n",
        "Notes to keep in mind:\n",
        "You can only use items that are in your possesion, ",
        "if you want to go somewhere, state the direction or the location in which you want to travel. ",
        "Actions should be atomic, not general and should interact with your immediate environment.",
        "Aim to keep action statements to 10 words or less",
        "Here is list of valid action verbs to use:\n",
        choices_str
    ])

    return system

def collect_system_info(game, character):
    previous_round = game.round - 1
    world_info = game.world_info
    agent_summary = character.persona.summary  # TODO: update this to match Louis' methodology
    if character.use_goals:
        agent_goals = str(character.goals.get_goals(round=previous_round))  # convert the dict to a string
    else:
        agent_goals = None

    system = ""

    if world_info:
        system += f"WORLD INFO: {game.world_info}\n"
    if agent_summary:
        system += f"You are {character.persona.summary}.\n"
    if agent_goals:
        system += f"Your current GOALS: {character.goals}.\n"
         
    system += "".join([
        "Given the context of your environment, past memories, ",
        "and interpretation of relationships with other characters,",
        "select a next action that advances your goals or strategy. "])
    
    return system

def build_user_message(game, character):
    # Add the theory of mind of agents that this agent has met
    impression_targets = character.get_characters_in_view(game)
    user_messages = character.impressions.get_multiple_impressions(impression_targets)

    # Retrieve the relevant memories to the situation
    user_messages += "These are select MEMORIES in ORDER from LEAST to MOST RELEVANT: " 
    context_list = retrieve(game, character, query=None, n=-1)

    if context_list:
        # Add a copy of the existing user message at the end of the memory context list 
        context_list.append(user_messages[:])

        # limit the context length here on the retrieved memories + the relationships
        context_list = limit_context_length(context_list, 
                                            max_tokens=GPT4_MAX_TOKENS-ACTION_MAX_OUTPUT, 
                                            tokenizer=game.parser.tokenizer)
        
        # Then add these to the user message after popping the user messsage off 
        context_list.pop()

        # print(f"passing {len(context_list)} relevant memories to {character.name}")
        user_messages += "".join([f"{m}\n" for m in context_list])
    
    return user_messages
