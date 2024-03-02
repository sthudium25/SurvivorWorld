"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/memory_structures/memory_stream.py
Description: Defines Agent memory classes
"""

# TODO: MemoryStream: list of ObservationNodes(Time, Place, Content, more?)
    # TODO: Node creation
        # TODO: node types (Dialogue, Action, Reflection, Event)
    # TODO: summarization of latest events
# TODO: split long and short-term memory structures like Joon Sung Park?

from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass, field    
from typing import List, Literal, Optional, Union
import openai
# from uuid import uuid4

# Local imports
from text_adventure_games.utils.gpt import gpt_agent as ga
# from text_adventure_games.things.characters import Character
from text_adventure_games.things.locations import Location


@dataclass
class ObservationNode:
    node_id: int  # TODO: should every node be unique, even across Agents?
    node_tick: int  # The round tick on which this observation occurred
    node_level: int  # The observation level: 1 for novel, 2 for reflections, 3 for ????
    node_round: int  # The round in which this occurred
    node_loc: str
    node_context: str
    subject: str
    node_type: str
    node_description: Optional[str] = field(default=None)
    embedding_key: int  # Immediately get and store the embedding for faster retrieval later?
    node_sentiment: int  # or could be float
    # agent_id: Optional[int] = field(default=None)  # ID of the agent making the observation, if relevant
    # associated_nodes: Optional[list[int]] = field(default_factory=list) 


class MemoryStream:
    def __init__(self, agent_id):
        self.num_observations = 0
        # TODO: this may be better as a dict of lists with keys as the round ID
        self.observations = []
        self.agent_id = agent_id  # would be good to store who this belongs to in case we need to reload a game
        self.obs_embeddings = {}
        self.nodes_by_subject = defaultdict(list)  # Nodes that appear to be related to the subject of the Observation
        self.nodes_by_type = defaultdict(list)

        # Attributes denoting the memory features of the agent
        self.lookback = 5  # The number of observations immediately available without retrieval
        self.gamma = 0.95  # The decay factor for memory importance
        self.reflection_capacity = 2  # The number of reflections to make after each round
        self.reflection_distance = 200  # how many observations the agent can look back and reflect on.
        self.reflection_rounds = 2  # The number of rounds the agent can look back
        
        # Attributes for calculating relevancy scores
        self.sentiment_alpha = 1
        self.recency_alpha = 1
        self.similarity_alpha = 1

    def get_observation(self, node_id):
        """
        Get the ith observation

        Args:
            node_id (int): the index of the requested ObservationNode

        Returns:
            ObservationNode: an ObservationNode
        """
        return self.observations[node_id]
    
    def add_dialogue(self,
                     round_tick: int,
                     game_round: int,
                     location: Location, 
                     dialogue: Dialogue,
                     description: str,
                     sentiment) -> None:
        
        node_id = self.num_observations + 1

        # TODO: parse Dialogue for speaker
        spoken_word = dialogue.dialogue
        speaker = dialogue.speaker

        # Get embedding of the dialoge
        dialogue_embedding = self.get_observation_embedding(dialogue)
        embed_key = f"{game_round}_{round_tick}"
        self.obs_embeddings[embed_key] = dialogue_embedding

        new_dialoge = ObservationNode(node_id,
                                      round_tick,
                                      game_round,
                                      location.name,
                                      node_level=1,
                                      node_context=spoken_word,
                                      subject=speaker,
                                      node_type="dialogue",
                                      node_description=description,
                                      embedding_key=embed_key,
                                      node_sentiment=sentiment)
        
        self.observations.append(new_dialoge)
        self.num_observations += 1

        # TODO: store anything else?
        self.nodes_by_subject[speaker].append(node_id)
        self.nodes_by_type['dialogue'].append(node_id)

    def add_reflection(self,
                       game_tick: int,
                       game_round: int,
                       location: Location, 
                       reflection: Reflection,
                       description: str,
                       sentiment) -> None:
        
        node_id = self.num_observations + 1

        reflection_embedding = self.get_observation_embedding(reflection)
        embed_key = f"{node_id}_{game_tick}"
        self.obs_embedding[embed_key] = reflection_embedding

        new_reflection = ObservationNode(node_id,
                                         game_tick,
                                         game_round,
                                         location.name,
                                         node_context=reflection.conclusion,
                                         subject=reflection.subject,
                                         node_type="reflection",
                                         node_description=description,
                                         embedding_key=embed_key,
                                         node_sentiment=sentiment)

        self.observations.append(new_reflection)
        self.num_observations += 1

        # TODO: add anything else?
        self.nodes_by_subject[reflection.subject].append(node_id)
        self.nodes_by_type['reflection'].append(node_id)

    def add_event(self,
                  game_tick: int,
                  location: Location, 
                  actor: Event,
                  description: str,
                  sentiment) -> None:
        # this will follow a similar structure to the methods above
        pass

    def get_observation_embedding(self, input):
        client = openai.Client()
        embedded_vector = ga.get_text_embedding(client, input)
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

    def get_embedding(self, round, tick):
        embed_key = f"{round}_{tick}"
        return self.obs_embeddings[embed_key]
