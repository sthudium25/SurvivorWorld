gpt_goals_prompt = """
\nUsing the context above that describes the world and yourself, as well as information you'll be provided about your past reflections and impressions of others, 
create high level goals at several priority levels for the next round. You can keep the previous goal, update the previous goal or create a new one based on your strategy.

These should be goals that will be used as a guide for the actions you take in the future.
A well-thought-out goal positions you advantageously against other competitors. Remember your primary objective is to not get voted out this round.
Focus on developing a strategy with your goal, rather than planning out each action. Keep the goals concise. 

Information about Goal Completion Score: On a scale of 1 to 5, this score shows if the goal was achieved or not with 1 being almost no progress towards the goal and 5 being goal completely achieved. 

The final output format should be the following:
Low Priority: 
Medium Priority: 
High Priority: 
"""


evaluate_goals_prompt = """
You are an impartial evaluator. On a scale of 1 to 5, give an integer for each priority tier that evaluates whether the goal was achieved or not with 1 being almost no progress towards the goal and 5 being goal completely achieved. 

The final output format should be the following:
High Priority: int
Medium Priority: int
Low Priority: int
"""
