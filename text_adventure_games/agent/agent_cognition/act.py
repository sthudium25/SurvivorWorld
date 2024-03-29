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
from text_adventure_games.gpt.gpt_helpers import gpt_pick_an_option, limit_context_length
from text_adventure_games.utils.general import set_up_openai_client, enumerate_dict_options
from .retrieve import retrieve

GPT4_MAX_TOKENS = 8192
ACTION_MAX_OUTPUT = 100


def act(game, character):
    available_actions = game.parser.actions

    system_prompt = "".join([
        # TODO: replace first line of prompt with more descriptive character summary
        f"You are {character.persona.summary}. ", 
        "Given the following context of your surroundings, past memories, ",
        "and relationships with other characters, select a next action that furthers your ",
        "strategic position in the game. "
    ])

    user_messages = ""
    # TODO: move game info and goals to the system_prompt?
    user_messages += f"WORLD INFO: {game.world_info}"
    user_messages += f"GOALS: {character.goals}. "
    # TODO: add personal relationships here as well
    # NOTE: For now we'll limit this to the default latest summary: last 10 memories
    # TODO: Add "short term memory" nodes by default?
    user_messages += "These are select MEMORIES in ORDER from LEAST to MOST RELEVANT: " 
    context_list = retrieve(game, character, query=None, n=-1)

    # limit the context length here on the retrieved memories
    context_list = limit_context_length(context_list, 
                                        max_tokens=GPT4_MAX_TOKENS-ACTION_MAX_OUTPUT, 
                                        tokenizer=game.parser.tokenizer)
    # Then add these to the user message
    print(f"passing {len(context_list)} relevant memories to {character.name}")
    user_messages += "".join([f"{m}\n" for m in context_list])

    action_to_take = generate_action(system_prompt, available_actions, user_messages)
    game.logger.debug(f"{character.name} chose to take action: {action_to_take}")
    print(f"{character.name} chose to take action: {action_to_take}")
    return action_to_take


def generate_action(system, game_actions, user):
    client = set_up_openai_client("Helicone")

    choices_str, _ = enumerate_dict_options(game_actions)
    system += "".join([
        "Using the information provided, generate a short action statement in the present tense from your perspective. ",
        "Be sure to mention any characters you wish to interact with by name. "
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

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=1,
        max_tokens=100,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response.choices[0].message.content
