"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: scales/traits.py
Description: Defines a TraitScale, which is score between two anchor words.
"""

from typing import List
from base import BaseScale
from ..utils.gpt import gpt_agent as ga


class TraitScale(BaseScale):
    """
    An extension of the base scale class providing the
    scale with a name and possibly other trait-specific attributes
    """

    MONITORED_TRAITS = {
        "judgement": ("Prejudicial", "Unbiased"),
        "cooperation": ("Stubborn", "Agreeable"),
        "outlook": ("Pessimistic", "Optimistic"),
        "initiative": ("Passive", "Assertive"),
        "generosity": ("Selfish", "Generous"),
        "social": ("Follower", "Learder"),
        "mind": ("Creative", "Logical"),
        "openness": ("Close-minded", "Open-minded"),
        "stress": ("Anxious", "Calm")
    }

    def __init__(self,
                 trait_name: str,
                 trait_dichotomy: BaseScale.Dichotomy,
                 score: int = 50,
                 min: int = 0,
                 max: int = 100):
        super().__init__(trait_dichotomy, score, min, max)
        self.name = trait_name
        self.adjective = None

    @classmethod
    def get_monitored_traits(cls) -> List:
        return cls.MONITORED_TRAITS

    def get_name(self) -> str:
        return self.name
    
    def update_score(self, new_score) -> None:
        self.score = new_score

    def set_adjective(self, model="gpt-3.5-turbo"):
        low, high = self.min_desciptor, self.max_desciptor
        adj = ga.get_target_adjective(low=low,
                                      high=high,
                                      target=self.score, 
                                      low_int=self.min, 
                                      high_int=self.max,
                                      model=model)
        self.adjective = adj

    def get_adjective(self):
        return self.adjective
        
    
