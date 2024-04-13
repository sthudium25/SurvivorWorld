"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/persona.py
Description: Defines the Persona of an agent
"""

# local imports
from text_adventure_games.gpt.gpt_agent_setup import summarize_agent_facts
from text_adventure_games.managers.scales import TraitScale
import json

class Persona():
    """
    Class to handle a character's persona.
    It will hold their Traits, Facts, and a summary of the character.

    A persona is an instance of an archetype
    It's initialized with a list of one or more archetypes to base the persona off of.

    Traits (dict): {trait name: TraitScale} on a scale from 0-100
    Facts (dict) these include the agent's name, age, occupation, likes, dislikes, and home city
    summary: str
    """
    def __init__(self, facts):
        # Agent traits
        self.facts = facts
        self.traits = {}
        self.summary = summarize_agent_facts(str(self.facts))
        self.description = f'A {self.facts["Age"]} year old {self.facts["Occupation"]} named {self.facts["Name"]}'
        self.game_theory_strategy = "nothing specific yet"
        self.strategy_in_effect = False

    def add_trait(self, trait):
        if trait.name not in self.traits:
            self.traits[trait.name] = trait

        # Set default game_theory_strategy based on "cooperation" trait
        if trait.name == "cooperation":
            if trait.score < 33:
                self.game_theory_strategy = "backstab"
            elif trait.score >= 34 and trait.score <= 66:
                self.game_theory_strategy = "tit-for-tat"
            else:
                self.game_theory_strategy = "cooperate"

    def get_trait_score(self, name: str):
        if name in self.traits:
            return self.traits[name].score
        
    def get_trait_summary(self):
        return [f"{tname} *tends* to be {self.traits[tname].get_adjective()}" for tname in self.traits]
    
    def start_strategy(self):
        self.strategy_in_effect = True

    def stop_strategy(self):
        self.strategy_in_effect = False

    def set_game_theory_strategy(self, strategy):
        self.game_theory_strategy = strategy

    # Export a persona into a json file ({person's name}.json)
    def export_persona(self):
        # Uniquely ID's persona by concatenated trait scores
        unique_id = ''.join(str(trait.score) for trait in self.traits.values())

        filedir = 'SurvivorWorld/text_adventure_games/assets/personas/'
        filename = self.facts['Name'] + "_" + unique_id + ".json"
        filepath = filedir + filename

        persona_dict = { # Convert the persona to a dictionary
            'traits': {tname: trait.__dict__ for tname, trait in self.traits.items()},
            'facts': self.facts,
            'summary': self.summary,
            'description': self.description,
            'strategy_in_effect': self.strategy_in_effect,
            'game_theory_strategy': self.game_theory_strategy,
        }

        with open(filepath, 'w') as f:
            json.dump(persona_dict, f)

        print(f"Successfully exported persona to {filepath}")

    # Import a persona from a file.
    @classmethod
    def import_persona(cls, filename):
        # Load the persona data from the JSON file
        with open(filename, 'r') as f:
            persona_dict = json.load(f)

        # Create a new Persona instance with the loaded data
        persona = cls(persona_dict['facts'])
        persona.traits = {tname: TraitScale(**trait) for tname, trait in persona_dict['traits'].items()}
        persona.summary = persona_dict['summary']
        persona.description = persona_dict['description']
        persona.strategy_in_effect = persona_dict['strategy_in_effect']
        persona.game_theory_strategy = persona_dict['game_theory_strategy']

        return persona
        
    # Made more natural-language friendly, not just a list of facts/traits, etc.
    def get_personal_summary(self):
        summary = f"Meet {self.facts['Name']}, a {self.facts['Age']}-year-old {self.facts['Occupation']}."
        if self.facts['Home city']:
            summary += f" They hail from {self.facts['Home city']}."
        if self.facts['Likes']:
            summary += f" {self.facts['Name']} is passionate about {', '.join(self.facts['Likes'][:3])}"
        if self.facts['Dislikes']:
            summary += f" but has aversions to {', '.join(self.facts['Dislikes'][:3])}."
        for key in self.facts:
            if key not in ['Name', 'Age', 'Occupation', 'Likes', 'Dislikes', 'Home city']:
                summary += f"{self.facts['Name'].title()}'s {key.lower()} is/are: {self.facts[key]}."
        if self.game_theory_strategy:
            summary += f" In the game, {self.facts['Name']}'s strategy is {self.game_theory_strategy},"
            summary += f" reflecting their {' and '.join(self.get_trait_summary())}."
        else: #Just list their traits
            summary += f" Their traits are: {', '.join(self.get_trait_summary())}."
        return summary

    def __str__(self):
        return self.get_personal_summary()