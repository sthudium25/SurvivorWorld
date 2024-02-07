from base import BaseScale
from ..things.characters import Character


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
