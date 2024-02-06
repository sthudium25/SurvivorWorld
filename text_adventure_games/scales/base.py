# Imports
from collections import namedtuple


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
        self.min_desciptor, self.max_desciptor = dichotomy
        self.min = min
        self.max = max
        self.score = score

    def __str__(self):
        # On a scale from 0 to 100, where 0 is evil and 100 is good, a score of 50
        # This wording was ranked most interpretable by GPT 3.5 and 4
        # over a number of trials
        return f"""On a scale from {self.min} to {self.max}, 
                   where {self.min} is {self.min_desciptor}
                   and {self.max} is {self.max_desciptor},
                   a score of {self.set_point}"""

    def update_score(self, delta: int):
        """
        Update the score of this scale by some delta
        It wiill be truncated to the scale limits

        Args:
            delta (int): _description_
        """
        if not isinstance(delta, int):
            raise TypeError("delta must be of type int")
        update = self.score + delta
        self.score = max(self.min, min(update, self.max))

    def get_score(self):
        return self.score
