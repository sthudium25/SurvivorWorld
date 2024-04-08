"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/persona.py
Description: Defines the Persona of an agent
"""

# local imports
from text_adventure_games.gpt.gpt_agent_setup import summarize_agent_facts
import json, random

class Persona():
    """
    Class to handle a character's persona.
    It will hold their Traits and Affinities

    A persona is an instance of an archetype
    It's initialized with a list of one or more archetypes to base the persona off of.

    Traits (dict): {trait name: TraitScale} on a scale from 0-100
    Facts (dict) these include the agent's name, age, occupation, likes, dislikes, and home city
    summary: str
    """
    # TODO, I'd like to be able to get multiple archetypes from build-agent
    def __init__(self, facts):
        # Agent traits
        self.facts = facts
        self.traits = {}
        self.summary = summarize_agent_facts(str(self.facts))
        self.description = f'A {self.facts["Age"]} year old {self.facts["Occupation"]} named {self.facts["Name"]}'

    def add_trait(self, trait):
        if trait.name not in self.traits:
            self.traits[trait.name] = trait

    def get_trait_score(self, name: str):
        if name in self.traits:
            return self.traits[name].score
        
    def get_trait_summary(self):
        return [f"{tname} TENDS TO BE {self.traits[tname].get_adjective()}" for tname in self.traits]
    
    # Method for saving the one or multiples personas to a Character
    # def save_persona(self,...

    # Method for loading the persona(s) from a Character
    # def load_persona(self,...
    
    # def get_goal_summary(self):
    #     goal_summary = ""
    #     goal_summary += f"to accomplish {self.goals['flex']}"
    #     goal_summary += f" but importantly must {self.goals['short-term']}."
    #     goal_summary += f" You goal for the entire game is to {self.goals['long-term']}."
    #     return goal_summary
        
    def get_personal_summary(self):
        summary = "Your name is"
        summary += f' {self.facts["Name"]} and you are {self.facts["Age"]} years old.'
        summary += f' You enjoy {" ".join(self.facts["Likes"][:3])}'
        summary += f' but dislike {" ". join(self.facts["Dislikes"][:3])}.'
        summary += f' Back home in {self.facts["Home city"]} you work as a {self.facts["Occupation"]}.'
        summary += f' Your {" ".join(self.get_trait_summary())}.'
        # summary += f' Your goals are {self.get_goal_summary()}'
        return summary
