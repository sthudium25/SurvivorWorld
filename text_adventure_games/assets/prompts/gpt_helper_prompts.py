
action_summary_prompt = """
Construct a cohesive summary of the information you're provided. You'll get information about the:
ACTOR: who initiated the action
LOCATION: where the action took place
ACTION: the action command
OUTCOME: the outcome

Use only the information contained in each information section, not the capitalized section identifiers themselves.
Create the summary using past tense.
If the outcome appears to be a dialogue between people, then focus on summarizing the most 
important parts of what they said. 
Always prefer to refer to characters by their names INSTEAD OF unspecific pronouns like "he", "they", "them", etcetera.
"""

action_importance_prompt = """
"You will be given a description of an action that someone took.
Gauge the importance of theirr action using provided description.
Return a score on a scale from 1 to 10, where 1 is mundane and 10 is critical."
"""
