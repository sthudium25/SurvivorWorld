"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/persona.py
Description: Defines the Persona of an agent
"""

# local imports
from text_adventure_games.gpt.gpt_agent_setup import summarize_agent_facts
#import gpt_helpers
from text_adventure_games.gpt.gpt_helpers import gpt_get_adjective_from_trait
import json, random

Trait_Name_Scales = {
    "judgement": {
        "lowAnchor": "Prejudicial",
        "highAnchor": "Unbiased"
    },
    "cooperation": {
        "lowAnchor": "Stubborn",
        "highAnchor": "Agreeable"
    },
    "outlook": {
        "lowAnchor": "Pessimistic",
        "highAnchor": "Optimistic"
    },
    "initiative": {
        "lowAnchor": "Passive",
        "highAnchor": "Assertive"
    },
    "generosity": {
        "lowAnchor": "Selfish",
        "highAnchor": "Generous"
    },
    "social": {
        "lowAnchor": "Follower",
        "highAnchor": "Leader"
    },
    "mind": {
        "lowAnchor": "Creative",
        "highAnchor": "Logical"
    },
    "openness": {
        "lowAnchor": "Close-minded",
        "highAnchor": "Open-minded"
    },
    "stress": {
        "lowAnchor": "Anxious",
        "highAnchor": "Calm"
    }
}

class Persona():
    """
    Class to handle a character's persona.
    It will hold their Traits and Affinities

    A persona is an instance of an archetype
    It's initialized with a list of one or more archetypes to base the persona off of.

    Traits (dict): {trait name: TraitScale} on a scale from 0-100
    Affinities (dict): {target character id: AffinityScale}
    Facts (dict)
    summary: str
    """
    def __init__(self, facts, archetypes):
        # Agent traits
        self.facts = facts
        self.archetypes = self.load_archetypes(archetypes)
        self.traits = self.add_traits_from_archetypes()
        self.affinities #These will be based on the likes/dislikes in facts
        self.summary = summarize_agent_facts(str(self.facts))
        self.description = f'A {facts["Age"]} year old {facts["Occupation"]} named {facts["Name"]}'

    def add_trait(self, trait):
        if trait.name not in self.traits:
            self.traits[trait.name] = trait

    def get_trait_score(self, name: str):
        if name in self.traits:
            return self.traits[name]["target_score"]
        
    def get_trait_summary(self):
        anchored_traits = [{"tname": tname, "score": score, 
                            "lowAnchor": Trait_Name_Scales[tname]['lowAnchor'],
                            "highAnchor": Trait_Name_Scales[tname]['highAnchor']}
                            for tname, score in self.traits.items()]
        return [f"{anchored_trait['tname']} TENDS TO BE {gpt_get_adjective_from_trait(anchored_trait)}"
                 for anchored_trait in anchored_traits]
    
    # Load the this personas archetypes from the json file
    def load_archetypes(self, archetypes):
        with open('SurvivorWorld/text_adventure_games/assets/archetypes.json', 'r') as f:
            all_archetypes = json.load(f)["archetypes"]
        return [archetype for archetype in all_archetypes if archetype["name"] in archetypes]

    # averages the traits found in the archetypes passed in
    def add_traits_from_archetypes(self):
        trait_scores = {}
        trait_counts = {}
        
        for archetype in self.archetypes:
            for trait in archetype["traits"]:
                if trait["name"] not in trait_scores:
                    trait_scores[trait["name"]] = 0
                    trait_counts[trait["name"]] = 0
                trait_scores[trait["name"]] += trait["targetScore"]
                trait_counts[trait["name"]] += 1

        # Randomly change each trait score to uniquely tailor each persona
        # They aren't cookie cut-outs of an archetype(s) 
        for trait in trait_scores:
            trait_scores[trait] += (0.5 - random.random()) * 10

        return {trait["name"]: trait_scores[trait] / trait_counts[trait] for trait in trait_scores}
    
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
        
    # def get_personal_summary(self):
    #     summary = "Your name is"
    #     summary += f' {self.facts["Name"]} and you are {self.facts["Age"]} years old.'
    #     summary += f' You enjoy {" ".join(self.facts["Likes"][:3])}'
    #     summary += f' but dislike {" ". join(self.facts["Dislikes"][:3])}.'
    #     summary += f' Back home in {self.facts["Home city"]} you work as a {self.facts["Occupation"]}.'
    #     summary += f' Your {" ".join(self.get_trait_summary())}.'
    #     # summary += f' Your goals are {self.get_goal_summary()}'
    #     return summary
