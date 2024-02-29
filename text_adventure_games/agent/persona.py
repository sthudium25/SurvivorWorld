"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/persona.py
Description: Defines the Persona of an agent
"""

class Persona():
    """
    Class to handle a character's persona.
    If will hold their Traits and Affinities

    Traits (dict): {trait name: TraitScale}
    Affinities (dict): {target character id: AffinityScale}
    Goals (dict): {maleable: generated ,
                   short-term: do not get voted off at the next tribal,
                   long-term: win the game and 1M dollars}
    """
    def __init__(self, facts, goals):
        self.facts = facts
        self.goals = goals
        self.traits = {}
        self.affinities = {}

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
