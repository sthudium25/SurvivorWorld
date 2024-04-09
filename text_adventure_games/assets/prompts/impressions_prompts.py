"""
Author: Samuel Thudium 

File: assets/prompts/impressions_prompts.py
Description: defines prompts used in the agent impressions module. 
             This module is used to develop a Theory of Mind of the other agents in the environment.
"""

gpt_impressions_prompt = """
World info: {world_info}

Personal info: {persona_summary}

Your job is to develop a theory of mind (ToM) for other another character. In doing so, consider the answers questions like:
- What do you think are the key strategies to win this game?
- Given how they have acted so far, what are their probable next moves?
- What are their impressions of you based on your interactions or second-hand knowledge of this person?
- Based on specific interactions or second-hand knowledge, do you consider this person trustworthy or not?
- What emotions does this person evoke for you?
- What are this person's motivations?
- Does this person have a close relationship with anyone else you know?

Generate a cohesive theory of mind when a presented with another person and the memories that you have of them. 

If you have already developed a theory of mind for this person, use new information or memories to update the ToM for the person focusing on any changes or new insights. 
This could include reflecting on your previous impressions and revising them if they have been proven to be incorrect.

Structure the theory of mind such that keys provide the aspect of ToM you are addressing and values elaborate on your understanding of that aspect with respect to this person. 

Here is a guide; keep each description concise:
Key Strategies: descriptions
Probable Next Moves: descriptions
{target_name}'s impressions of you: descriptions
Trustworthiness: descriptions
Personal Feelings/Emotions: descriptions
Motivations: descriptions
Relationships: descriptions
"""
