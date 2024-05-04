"""
Author: Samuel Thudium 

File: assets/prompts/reflection_prompts.py
Description: defines prompts used in the agent reflection module
"""

# gpt_generalize_prompt = """
# You are an agent in a game and you need to reflect upon your previous observations to improve your understanding of the environment
# and how to act within it. This could also include considering how to improve your past actions to be more efficient with respect to achieving your goals. 
# You'll be given a list of action statements that you and other agents around you have made. 
# You'll also be able to see past reflections you have made. 

# From the new actions, try to:
# 1. identify only the most impactful new generalizations about your actions or the environment. 
# 2. update or elaborate upon previous reflections.

# For each reflective statement you make, mimic one of the following structures that capture the logic of necessity or entailment:

# x MAY BE NECESSARY FOR y
# x IS NECESSARY AND SUFFICIENT FOR y
# x IS NOT NECESSARY FOR y
# x COULD AFFECT y
# x DOES NOT AFFECT y
# x ENTAILS y
# x DOES NOT ENTAIL y

# You can add or remove negation from any of the statements in order to ensure the truthiness of the end statement.

# Separate your new and revised reflections. 
# Prior reflections are each associated with an id; if you update a reflection use this id as the key for the statement that you have updated. 
# Return a JSON structure like:
# {"new": [
#     {"index": an integer,
#      "statement": "a new generalized knowledge statement"
#     }],
# "updated": [
#     {"index": index of prior statement, 
#      "statement": "updated/revised knowledge statement"
#     }]  
# }

# Remember, make generalized statements that are rooted in the facts you're provided. 
# Keep statements short where possible. Only capitalize the relationship words, not the whole sentence.
# """

gpt_generalize_prompt = """
Based on your character and goals described above, you need to reflect upon your previous reflections and observations to improve your understanding of the environment and how to act within it.
This could also include considering how to improve your past actions to be more efficient with respect to achieving your goals. 
You'll be given your current impressions of all other agents, your prior reflections, and action statements that you and other agents around you have made.

From these impressions, reflections, and memories, try to:
1. identify only the most impactful new elaborations on previous reflections or new generalizations about your actions or the environment.
2. update previous reflections if they no longer appear to be true.

Separate your new and revised reflections.
Prior reflections are each associated with an id; if you update a reflection use this id as the key for the statement that you have updated. 
Only return a JSON object, using the following structure:
{"new": [
    {"statement": "a new generalized knowledge statement"
    }],
"updated": [
    {"index": index of prior statement,
     "statement": "updated/revised knowledge statement"
    }]
}

Remember, make generalized statements that are rooted in the facts you're been provided, and only update past reflections if they no longer seem accurate.
"""

# EXPLORATION
memory_query_questions = [
    "What have I been doing to achieve the goal of the game?",
    "Which locations, actions or items seem important or helpful to the goal of the game?",
    "Which locations, actions or items seem unimportant or detrimental to the goal of the game?",
    "Which strategies have been effective so far, and how should I adjust my overall game plan to align with the evolving dynamics of the game?"
]

insight_question = "What five high-level insights can you infer from the above statements? You can make new and/or updated generalizations, but there should be no more than five in total."
