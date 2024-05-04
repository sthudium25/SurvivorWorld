gpt_goals_prompt = """
\nUsing the context above that describes the world and yourself, as well as information you'll be provided about your past reflections and impressions of others, 
create high level goals at several priority levels for the next round. You can keep the previous goal, update the previous goal or create a new one based on your strategy.

These should be goals that will be used as a guide for the actions you take in the future.
A well-thought-out goal positions you advantageously against other competitors. Remember your overarching objective is to find the idol.
Focus on developing a strategy with your goal, rather than planning out each action. Keep the goals concise. 

You may see your previous goals as well as an accompanying Goal Completion Score, which is on a scale of 1 to 5.
This score tells you how well your actions advanced completion of the goal, with 1 meaning almost no progress was made towards the goal and 5 meaning the goal was completely achieved. 
If you see these scores, consider updating your goals accordingly.
A low score could indicate you haven't been working toward the goal or that the goal is very difficult to achieve.
A high score indicates you've successfully achieved the goal and should think about your next strategic target.
You must only use the scoring information in deciding how to update your goals, but do not add a score into your goals.

If you want to keep working toward a previous goal, just write it out again.

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
