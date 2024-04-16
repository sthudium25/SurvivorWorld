"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/persona.py
Description: Defines the Persona of an agent
"""

# local imports
from text_adventure_games.gpt.gpt_agent_setup import summarize_agent_facts
from text_adventure_games.managers.scales import TraitScale
import json
import os

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
        self.speaking_style = ""

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
        return [f"{tname} which *tends* to be {self.traits[tname].get_adjective()}" for tname in self.traits]
    
    def start_strategy(self):
        self.strategy_in_effect = True

    def stop_strategy(self):
        self.strategy_in_effect = False

    def set_game_theory_strategy(self, strategy):
        self.strategy_in_effect = True
        self.game_theory_strategy = strategy

    # Export a persona into a json file ({person's name}.json)
    def export_persona(self):
        # Uniquely ID's persona by concatenated trait scores
        unique_id = ''.join("{:02d}".format(int(trait.score)) for trait in self.traits.values())

        #filedir = '../../SurvivorWorld/text_adventure_games/assets/personas/'
        filedir = './game_personas/'
        if not os.path.isdir(filedir):
            os.makedirs(filedir, exist_ok=True)

        filename = self.facts['Name'] + "_" + unique_id + ".json"
        filepath = filedir + filename

        persona_dict = { # Convert the persona to a dictionary
            'traits': {tname: {'score': trait.score, 'adjective': trait.adjective} for tname, trait in self.traits.items()},
            'facts': self.facts,
            'fact_summary': self.summary,
            'persona_summary': self.get_personal_summary(),
            'description': self.description,
            'strategy_in_effect': self.strategy_in_effect,
            'game_theory_strategy': self.game_theory_strategy,
        }

        with open(filepath, 'w') as f:
            json.dump(persona_dict, f, indent=4)

        print(f"Successfully exported persona to {filepath}")

    # Import a persona from a file.
    # NOTE: This does *not* allow you to cross-import personas from different people, since
    # it copies their facts as well. 
    @classmethod
    def import_persona(cls, filename):
        # Load the persona data from the JSON file
        with open(filename, 'r') as f:
            persona_dict = json.load(f)

        # Create a new Persona instance with the loaded data
        persona = cls(persona_dict['facts'])
        #persona.traits = {tname: {'score': trait['score'], 'adjective': trait['adjective']} for tname, trait in persona_dict['traits'].items()}
        #persona.traits = {tname: TraitScale(**trait) for tname, trait in persona_dict['traits'].items()}
        persona.summary = persona_dict['fact_summary']
        persona.description = persona_dict['description']
        persona.strategy_in_effect = persona_dict['strategy_in_effect']
        persona.game_theory_strategy = persona_dict['game_theory_strategy']

        monitored_traits = TraitScale.get_monitored_traits()
        for tname, trait in persona_dict['traits'].items():
            trait_dichotomy = monitored_traits[tname]
            persona.traits[tname] = TraitScale(tname, trait_dichotomy, score=trait['score'], adjective=trait['adjective'])

        return persona
    
    # Make a string describing the persona's speaking style, instructing chatGPT how to speak.
    def get_speaking_style(self):
        # If we've already generated the speaking style, return it
        if self.speaking_style:
            return self.speaking_style
        
        style = f"Speaks in the style of a {self.facts['Age']} year old {self.facts['Occupation']} from {self.facts.get('Home city', 'no place in particular')}. "
        
        # Get 'outlook' and 'stress' traits to include in their speaking style.
        outlook = self.get_trait_score('outlook')
        stress = self.get_trait_score('stress')

        # Determine the speaking style based on the traits
        if outlook > 66:
            style += "They're generally optimistic and have a positive outlook on life. "
        elif outlook < 33:
            style += "They're generally pessimistic and have a negative outlook on life. "
        else:
            style += "They have a balanced outlook on life. "

        if stress > 66:
            style += "They're often stressed and anxious. "
        elif stress < 33:
            style += "They're often calm and relaxed. "
        else:
            style += "They're generally balanced in their stress levels. "

        style += "Use this information to guide how they speak, in terms of tone, word choice, sentence structure, \
            phrasing, terseness, verbosity, and overall demeanor."

        self.speaking_style = style

        return style
        
    # Made more natural-language friendly, not just a list of facts/traits, etc.
    def get_personal_summary(self):
        summary = f"Meet {self.facts['Name']}, a {self.facts['Age']}-year-old {self.facts['Occupation']}."
        if 'Home city' in self.facts and self.facts['Home city']:
            summary += f" They hail from {self.facts['Home city']}."
        if 'Likes' in self.facts and self.facts['Likes']:
            summary += f" {self.facts['Name']} is passionate about {', '.join(self.facts['Likes'][:3])}"
        if 'Dislikes' in self.facts and self.facts['Dislikes']:
            summary += f" but has aversions to {', '.join(self.facts['Dislikes'][:3])}."
        for key in self.facts:
            if key not in ['Name', 'Age', 'Occupation', 'Likes', 'Dislikes', 'Home city']:
                summary += f"{self.facts['Name'].title()}'s {key.lower()} is/are: {self.facts[key]}."
        if self.game_theory_strategy:
            summary += f" In the game, {self.facts['Name']}'s strategy is {self.game_theory_strategy},"
            traits = self.get_trait_summary()
            summary += f" reflecting their {', '.join(traits[:-1])} and {traits[-1]}."
        else: #Just list their traits
            traits = self.get_trait_summary()
            summary += f" Their traits are {', '.join(traits[:-1])} and {traits[-1]}."
        return summary

    def __str__(self):
        return self.get_personal_summary()