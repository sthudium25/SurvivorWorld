"""
Author: Federico Cimini

File: assets/prompts/dialogue_prompt.py
Description: defines prompts used in the dialogue class.
"""

gpt_dialogue_prompt = """
You are in dialogue with: {other_character}.
When it's your turn to speak, you can say something or walk away form the conversation.

If you say something, start with: '{character} says: '.

If you walk away, say only: '{character} leaves the conversation.'.

Do not return anything besides those two options.
If you feel like the last two lines have not added new information or people are speaking in circles, end the conversation.

"""