"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/memory_structures/memory_stream.py
Description: Defines Agent memory classes
"""
from __future__ import annotations
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass, field    
import re
from typing import List, Literal, Optional, Union
import openai
# from uuid import uuid4

# Local imports
from ..gpt import gpt_agent_setup as ga
from ..utils.general import set_up_openai_client
from spacy import load as spacyload


class MemoryType(Enum):
    ACTION = 1
    DIALOGUE = 2
    REFLECTION = 3


@dataclass
class ObservationNode:
    node_id: int  # TODO: unique to this agent; represents the index in their memory
    # node_tick: int  # The round tick on which this observation occurred
    # node_round: int  # The round in which this occurred
    node_level: int  # The observation level: 1 for novel, 2 for reflections, 3 for ????
    node_loc: str
    node_description: str
    node_success: bool
    embedding_key: int  # Immediately get and store the embedding for faster retrieval later?
    node_importance: int  # or could be float
    node_type: str = None  # the type of Observation
    # agent_id: Optional[int] = field(default=None)  # ID of the agent making the observation, if relevant
    # associated_nodes: Optional[list[int]] = field(default_factory=list) 


class MemoryStream:
    # store stopwords as a class variable for efficient access when adding new memories
    _stopwords = None

    @classmethod
    def _generate_stopwords(cls):
        if cls._stopwords is None:
            nlp = spacyload('en_core_web_sm', disable=['ner', 'tagger', 'parser', 'textcat'])
            cls._stopwords = nlp.Defaults.stop_words
        return cls._stopwords

    def __init__(self, agent_id, agent_name, agent_description):
        """
        Defines Agent's memory via a dict of ObservationNodes. These
        are split by the round in which they occured.

        Args:
            agent_id (int): thing.Thing.id for this agent
        """
        # keep track of this agent's identifying info:
        self.agent_id = agent_id  # would be good to store who this belongs to in case we need to reload a game
        self.agent_name = agent_name
        self.agent_description = agent_description
        
        self.num_observations = 0
        self.observations = []
        
        self.memory_embeddings = {}  # keys are the index of the observation
        self.character_nodes = defaultdict(list)  # Nodes that appear to be related to a character
        self.object_nodes = defaultdict(list)
        self.misc_keyword_nodes = defaultdict(list)

        # Attributes defining the memory features of the agent
        self.lookback = 10  # The number of observations immediately available without retrieval
        self.gamma = 0.95  # The decay factor for memory importance
        self.reflection_capacity = 2  # The number of reflections to make after each round
        self.reflection_distance = 200  # how many observations the agent can look back and reflect on.
        self.reflection_rounds = 2  # The number of rounds the agent can look back
        
        # Attributes for calculating relevancy scores
        self.sentiment_alpha = 1
        self.recency_alpha = 1
        self.similarity_alpha = 1

        # Set up a client for this instance
        self.client = set_up_openai_client(org="Penn")

        # Initialize stopwords
        self.stopwords = self._generate_stopwords()

    def get_observation(self, node_id):
        """
        Get the ith observation

        Args:
            node_id (int): the index of the requested ObservationNode

        Returns:
            ObservationNode: an ObservationNode
        """
        return self.observations[node_id]
    
    def add_memory(self,
                   description,
                   keywords,
                   location,
                   success_status,
                   memory_importance,
                   memory_type):
        
        if not isinstance(memory_type, MemoryType):
            valid_types = [type.name for type in MemoryType]
            raise ValueError(f"Memories must be created with valid type; one of {valid_types}")
            
        # Get the next node id
        node_id = self.num_observations + 1
        
        # Modify the description w.r.t this character's name
        description = self.replace_character(description, 
                                             self.agent_name.lower(), 
                                             agent_descriptor=self.agent_description)

        # Embed the description
        memory_embedding = self.get_observation_embedding(description)
        self.memory_embeddings[node_id] = memory_embedding

        if memory_type == MemoryType.ACTION:
            new_memory = self.add_action(node_id,
                                         description,
                                         location,
                                         success_status,
                                         memory_importance,
                                         type=MemoryType.ACTION)
        
        # Add node to sequential memory
        self.observations.append(new_memory)

        # Cache the node under its keywords
        # TODO: weigh the pros/cons of adding these at start vs. end of the kwd list
        for category, kws_list in keywords.items():
            if category == "characters":
                for kw in kws_list:
                    self.character_nodes[kw].append(node_id)
            elif category == "object":
                for kw in kws_list:
                    self.object_nodes[kw].append(node_id)
            else:
                for kw in kws_list:
                    self.misc_keyword_nodes[kw].append(node_id)
        
        # increment the internal count of nodes
        self.num_observations += 1
            
    def add_action(self,
                   node_id,
                   description,
                   location: str,
                   success_status: bool,
                   memory_importance: int,
                   type: MemoryType) -> None:
        
        new_action = ObservationNode(node_id,
                                     node_level=1,
                                     node_loc=location,
                                     node_description=description,
                                     node_success=success_status,
                                     embedding_key=node_id,
                                     node_importance=memory_importance,
                                     node_type=type)
        # print(f"Added {new_action.node_description} to {self.agent_id}'s memory")
        return new_action

    def get_observation_embedding(self, text):
        """
        Embed the text of an observation

        Args:
            text (str): the text to embed

        Returns:
            ndarray: an embedding vector
        """
        embedded_vector = ga.get_text_embedding(text)
        return embedded_vector
    
    def get_observations_by_subject(self, subject):
        return self.nodes_by_subject[subject]
    
    def get_observations_by_type(self, obs_type):
        return self.nodes_by_type[obs_type]
    
    def get_most_recent_summary(self):
        nodes = self.observations[-self.lookback:]
        summary = f"The last {self.lookback} observations in chronological order you have made are:"
        for i, node in enumerate(nodes):
            summary += "\n{idx}. {desc}".format(idx=i, desc=node.node_description)
        return summary

    def get_embedding(self, round, tick):
        embed_key = f"{round}_{tick}"
        return self.obs_embeddings[embed_key]
    
    def replace_character(self, text, character_name, agent_descriptor):
        # Escape any special regex characters in the descriptor and character_name
        escaped_name = re.escape(character_name)
        escaped_descriptor = re.escape(" ".join([w for w in agent_descriptor.split() if w not in self.stopwords]))
        # Pattern to match 'the' optionally, then the descriptor optionally, followed by the character name
        # The descriptor and the character name can occur together or separately
        pattern = r'\b(?:the\s+)?(?:(?:{d}\s+)?{c}|{d})\b'.format(d=escaped_descriptor, c=escaped_name)
        replacement = 'you'
        return re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # def add_dialogue(self,
    #                  round_tick: int,
    #                  game_round: int,
    #                  location: Location, 
    #                  dialogue: str,
    #                  description: str,
    #                  sentiment) -> None:
        
    #     node_id = self.num_observations + 1

    #     # TODO: parse Dialogue for speaker
    #     spoken_word = dialogue.dialogue
    #     speaker = dialogue.speaker

    #     # Get embedding of the dialoge
    #     dialogue_embedding = self.get_observation_embedding(dialogue)
    #     embed_key = f"{game_round}_{round_tick}"
    #     self.obs_embeddings[embed_key] = dialogue_embedding

    #     new_dialoge = ObservationNode(node_id,
    #                                   round_tick,
    #                                   game_round,
    #                                   location.name,
    #                                   node_level=1,
    #                                   node_context=spoken_word,
    #                                   subject=speaker,
    #                                   node_type="dialogue",
    #                                   node_description=description,
    #                                   embedding_key=embed_key,
    #                                   node_sentiment=sentiment)
        
    #     self.observations.append(new_dialoge)
    #     self.num_observations += 1

    #     # TODO: store anything else?
    #     self.nodes_by_subject[speaker].append(node_id)
    #     self.nodes_by_type['dialogue'].append(node_id)

    # def add_reflection(self,
    #                    game_tick: int,
    #                    game_round: int,
    #                    location: Location, 
    #                    reflection: Reflection,
    #                    description: str,
    #                    sentiment) -> None:
        
    #     node_id = self.num_observations + 1

    #     reflection_embedding = self.get_observation_embedding(reflection)
    #     embed_key = f"{node_id}_{game_tick}"
    #     self.obs_embedding[embed_key] = reflection_embedding

    #     new_reflection = ObservationNode(node_id,
    #                                      game_tick,
    #                                      game_round,
    #                                      location.name,
    #                                      node_context=reflection.conclusion,
    #                                      subject=reflection.subject,
    #                                      node_type="reflection",
    #                                      node_description=description,
    #                                      embedding_key=embed_key,
    #                                      node_sentiment=sentiment)

    #     self.observations.append(new_reflection)
    #     self.num_observations += 1

    #     # TODO: add anything else?
    #     self.nodes_by_subject[reflection.subject].append(node_id)
    #     self.nodes_by_type['reflection'].append(node_id)
