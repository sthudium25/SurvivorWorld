"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/persona.py
Description: Defines the Persona of an agent
"""

# local imports
from . import memory_stream as ms
from text_adventure_games.gpt.gpt_agent_setup import summarize_agent_facts


class Persona():
    """
    Class to handle a character's persona.
    It will hold their Traits and Affinities

    Traits (dict): {trait name: TraitScale}
    Affinities (dict): {target character id: AffinityScale}
    Goals (dict): {flex: generated,
                   short-term: do not get voted off at the next tribal,
                   long-term: win the game and 1M dollars}
    Facts (dict)
    summary: str
    """
    def __init__(self, facts, goals):
        # Agent traits
        self.facts = facts
        self.goals = goals
        self.traits = {}
        self.affinities = {}
        self.summary = summarize_agent_facts(self.facts)

    # NOTE: Removing this for now -- memory stored in GenerativeAgent()
    # def initialize_memory(self, agent_id):
    #     # Agent Memory
    #     self.memory = ms.MemoryStream(agent_id)

    def add_trait(self, trait):
        if trait.name not in self.traits:
            self.traits[trait.name] = trait

    def add_affinity(self, affinity):
        if affinity.target.id not in self.affinities:
            self.affinities[affinity.target.id] = affinity

    def get_trait_score(self, name: str):
        if name in self.traits:
            return self.traits[name].get_score()

    def get_affinity_score(self, target_id: str):
        if target_id in self.affinities:
            return self.affinities[target_id].get_score()
        
    def get_trait_summary(self):
        return [f"{tname} is {trait.adjective}" for tname, trait in self.traits.items()]
    
    def get_goal_summary(self):
        goal_summary = ""
        goal_summary += f"to accomplish {self.goals['flex']}"
        goal_summary += f" but importantly must {self.goals['short-term']}."
        goal_summary += f" You goal for the entire game is to {self.goals['long-term']}."
        return goal_summary
        
    def get_personal_summary(self):
        summary = "Your name is"
        summary += f' {self.facts["Name"]} and you are {self.facts["Age"]} years old.'
        summary += f' You enjoy {" ".join(self.facts["Likes"][:3])}'
        summary += f' but dislike {" ". join(self.facts["Dislikes"][:3])}.'
        summary += f' Back home in {self.facts["Home city"]} you work as a {self.facts["Occupation"]}.'
        summary += f' Your {" ".join(self.get_trait_summary())}.'
        summary += f' Your goals are {self.get_goal_summary()}'
        return summary
