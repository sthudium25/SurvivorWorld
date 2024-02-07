from ..scales import traits, affinity


class PersonaManager():
    """
    Class to handle a character's persona.
    If will hold their Traits and Affinities

    Traits (dict): {trait name: TraitScale}
    Affinities (dict): {target character id: AffinityScale}
    """
    def __init__(self):
        self.traits = {}
        self.affinities = {}

    def add_trait(self, trait: traits.TraitScale):
        if trait.name not in self.traits:
            self.traits[trait.name] = trait

    def add_affinity(self, affinity: affinity.AffinityScale):
        if affinity.target.id not in self.affinities:
            self.affinities[affinity.target.id] = affinity

    def get_trait_score(self, name: str):
        if name in self.traits:
            return self.traits[name].get_score()

    def get_affinity_score(self, target_id: str):
        if target_id in self.affinities:
            return self.affinities[target_id].get_score()
        
    