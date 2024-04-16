# Imports
from collections import namedtuple
from typing import List

# local imports
from ..gpt.gpt_agent_setup import get_target_adjective
from ..things.characters import Character


class BaseScale:
    """
    Base scale class providing the basic definition of a
    numeric scale between two ends of a spectrum

    Since the end goal is to use this game with a language model
    agent, I want to enforce scales as having a descriptor
    for the low and the high points.

    These will be accessed and allow interpretation of the set point
    in context.
    """
    Dichotomy = namedtuple("Scale", ['min', 'max'])

    def __init__(self,
                 dichotomy: Dichotomy,
                 score: int = 50,
                 min: int = 0,
                 max: int = 100):
        self.min_descriptor, self.max_descriptor = dichotomy
        self.min = min
        self.max = max
        self.score = score

    def __str__(self):
        # On a scale from 0 to 100, where 0 is evil and 100 is good, a score of 50
        # This wording was ranked most interpretable by GPT 3.5 and 4
        # over a number of trials
        return f"""On a scale from {self.min} to {self.max}, 
        where {self.min} is {self.min_descriptor}
        and {self.max} is {self.max_descriptor},
        a score of {self.score}"""

    def update_score(self, delta: int):
        """
        Update the score of this scale by some delta
        It will be truncated to the scale limits

        Args:
            delta (int): _description_
        """
        if not isinstance(delta, int):
            raise TypeError("delta must be of type int")
        update = self.score + delta
        self.score = max(self.min, min(update, self.max))

    def get_score(self):
        return self.score


class AffinityScale(BaseScale):
    """
    An extension of the base scale class providing the
    affinity that two characters have for one another.
    """

    def __init__(self,
                 character: Character,
                 dichotomy: BaseScale.Dichotomy,
                 score: int = 50,
                 min: int = 0,
                 max: int = 100,
                 visibile: bool = False):
        super().__init__(dichotomy, score, min, max)
        self.target = character
        self.visible = visibile

    def get_visibility(self):
        return self._visibile

    def set_visibility(self):
        self.visible = not self.visible


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
        "social": ("Follower", "Leader"),
        "mind": ("Creative", "Logical"),
        "openness": ("Close-minded", "Open-minded"),
        "stress": ("Anxious", "Calm")
    }

    def __init__(self,
                 trait_name: str,
                 trait_dichotomy: BaseScale.Dichotomy,
                 score: int = 50,
                 min: int = 0,
                 max: int = 100,
                 adjective: str = None):
        super().__init__(trait_dichotomy, score, min, max)
        self.name = trait_name
        self.adjective = adjective

    @classmethod
    def get_monitored_traits(cls) -> List:
        return cls.MONITORED_TRAITS

    def get_name(self) -> str:
        return self.name
    
    def update_score(self, new_score) -> None:
        self.score = new_score

    def set_adjective(self, model="gpt-3.5-turbo"):
        low, high = self.min_descriptor, self.max_descriptor
        adj = get_target_adjective(low=low,
                                   high=high,
                                   target=self.score, 
                                   low_int=self.min, 
                                   high_int=self.max,
                                   model=model)
        self.adjective = adj

    def get_adjective(self):
        return self.adjective
