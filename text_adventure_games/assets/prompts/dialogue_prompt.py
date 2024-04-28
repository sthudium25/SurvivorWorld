"""
Author: Federico Cimini

File: assets/prompts/dialogue_prompt.py
Description: defines prompts used in the dialogue class.
"""

gpt_dialogue_system_prompt = """
You are in dialogue with: {other_character}.
When it's your turn to speak, you can say something or walk away form the conversation.
Respond strategically. If it is not advantageous to agree with the person you're talking to, then don't.

If you say something, just say what you would say if you were replying directly to the dialogue.
Don't add your name before the line of dialogue. Only output the line of dialogue.

If you walk away, say only: 'I leave the conversation.'.

Do not return anything besides those two options.
If you feel like the last two lines have not added new information or people are speaking in circles, end the conversation.
"""

gpt_dialogue_user_prompt = """
Dialogue history:

{dialogue_history}

What do you say next? Alternatively, do you leave the conversation?
"""
