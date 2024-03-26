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
# 3. Learning generalization
#   - CLIN style generation of relationships between actions and outcomes (i.e. x MAY BE NECESSARY for y)
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


def reflect():
    pass
