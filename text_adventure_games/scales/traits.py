from base import BaseScale


class TraitScale(BaseScale):
    """
    An extension of the base scale class providing the
    scale with a name and possibly other trait-specific attributes
    """

    def __init__(self,
                 trait_name: str,
                 dichotomy: BaseScale.Dichotomy,
                 score: int = 50,
                 min: int = 0,
                 max: int = 100):
        super().__init__(dichotomy, score, min, max)
        self.name = trait_name

    def get_name(self):
        return self.name