
vote_system_ending = """
You are currently in a voting round so you must vote for another contestant you want to take out of the game. 
Use the provided information about yourself, your position in the game, and your goals. 
You will also see information about your relationships and memories.
Use this context to cast a vote that you believe will do the most to improve your position in the game. 
Weight or interpret the memories based on their influence of the voting decision you need to make.
This could mean sticking with an alliance or being deceitful, the choice is up to you. 
Respond with the name of the contestant you are voting to kick out and give an breif explanation (1 to 2 sentences) why you've chosen them as the target of your vote.

Example response in JSON format.

{"target": "Elias Whitaker",
 "reason": "Elias is a strong player with numerous allicances. If he makes it to the finale, he is very likely to win over the jury"
 }
"""

vote_user_prompt = """
You are in a voting round of the game, so you must select another contestant to vote off the tribe. 
This person will be out of the game for good, but they may be able to cast a vote to help
determine the final winner of the game.

Given your knowledge of the game, yourself, and the other players, select one of the following
players to vote for:
{vote_options}

Who will you vote for and why did you choose to vote for them? Remember to use JSON format with your "target" and "reason" as keys. 
"""

jury_system_ending = """
You are currently at the final tribal council so you must vote for one of the finalists to win the game. 
Use your knowledge of the finalists gameplay, your interactions with them, and your personal feelings about them 
to cast a vote for the most deserving winner. 
Respond with the name of the contestant you are voting for and give an explanation why you've chosen them as the winner of the game.

Example response in JSON format.

{"target": "Elias Whitaker",
 "reason": "Elias is a strong player who has played with strong strategy throughout the game. I like his style and respect him."
 }
"""

jury_user_prompt = """
You are in the final round of the game, so you must select a finalist as the winner. 
This person will be win the game overall!

Given your knowledge of the game, yourself, and the finalists, select one of the following
players to name as winner:
{vote_options}

Who will you vote for and why did you choose to vote for them? Remember to use JSON format with your "target" and "reason" as keys. 
"""

winner_memory_description = """
{winner} won the game by recieving {for_votes} out of {total_votes}!!!
"""

immunity_memory_prompt = "The following players found a hidden immunity idol, making them safe from the vote this round: {immune_players}"
