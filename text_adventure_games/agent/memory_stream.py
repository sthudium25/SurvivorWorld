"""
Author: Samuel Thudium (sam.thudium1@gmail.com)

File: agent/memory_structures/memory_stream.py
Description: Defines Agent memory classes
"""
from __future__ import annotations
from typing import TYPE_CHECKING, List, Literal, Tuple, Union
from enum import Enum
from collections import defaultdict
from dataclasses import dataclass, field
import re
from spacy import load as spacyload
# from uuid import uuid4

# Local imports
from ..utils.general import set_up_openai_client, get_text_embedding
if TYPE_CHECKING:
    from ..things.characters import Character

class MemoryType(Enum):
    ACTION = 1
    DIALOGUE = 2
    REFLECTION = 3
    PERCEPT = 4

@dataclass
class ObservationNode:
    node_id: int  # TODO: unique to this agent; represents the index in their memory
    node_round: int  # The round in which this occurred
    node_tick: int  # The round tick on which this observation occurred
    node_level: int  # The observation level: 1 for novel, 2 for reflections, 3 for ????
    node_loc: str  # The name of the location in which the observation occurred
    node_description: str
    node_success: bool
    embedding_key: int  # Immediately get and store the embedding for faster retrieval later?
    node_importance: int  # or could be float
    node_is_self: int  # ID of the agent making the observation, if relevant
    node_type: str = None  # the type of Observation
    node_keywords: set = field(default_factory=set)  # Keywords that were discovered in this node
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

    def __init__(self, character: "Character"):
        """
        Defines Agent's memory via a dict of ObservationNodes. These
        are split by the round in which they occured.

        Args:
            agent_id (int): thing.Thing.id for this agent
        """
        # keep track of this agent's identifying info:
        self.agent_id = character.id  # would be good to store who this belongs to in case we need to reload a game
        self.agent_name = character.name
        self.agent_description = character.description
        
        self.num_observations = 0
        self.observations = []
        
        self.memory_embeddings = {}  # keys are the index of the observation
        self.keyword_nodes = defaultdict(lambda: defaultdict(list))
        self.memory_type_nodes = defaultdict(list)  # keys are the value of the MemoryType enum
        self.this_round_nodes = defaultdict(list)  # keys are the round number

        # A cache of the current querying statements about this agent
        # Cached embeddings of: Persona summary, goals, personal relationships
        # These will be used in the memory retrieval process
        self.query_embeddings = self.set_query_embeddings(character)

        # Attributes defining the memory features of the agent
        self.lookback = 5  # The number of observations immediately available without retrieval; also used to gather keys for retrieval
        self.gamma = 0.95  # The decay factor for memory importance
        self.reflection_capacity = 2  # The number of reflections to make after each round
        self.reflection_distance = 200  # how many observations the agent can look back and reflect on.
        self.reflection_rounds = 2  # The number of rounds the agent can look back
        
        # Attributes for calculating relevancy scores
        self.importance_alpha = 1
        self.recency_alpha = 1
        self.relevance_alpha = 1

        # Set up a client for this instance
        self.client = set_up_openai_client(org="Penn")

        # Initialize stopwords
        self.stopwords = self._generate_stopwords()

    # ----------- MEMORY CREATION -----------
    def add_memory(self,
                   round,
                   tick,
                   description,
                   keywords,
                   location,
                   success_status,
                   memory_importance,
                   memory_type,
                   actor_id):
        
        if not self.is_valid_memory_type(memory_type):
            valid_types = [type.name for type in MemoryType]
            raise ValueError(f"Memories must be created with valid type; one of {valid_types}")
            
        # Get the next node id
        # This works out to be the number of observations b/c of zero-indexing
        node_id = self.num_observations
        
        # Modify the description w.r.t this character's name
        # description = self.replace_character(description, 
        #                                      self.agent_name.lower(), 
        #                                      agent_descriptor=self.agent_description)
        
        # Get a flattened list of keywords found in this memory
        node_kwds = [w for kw_type in keywords.values() for w in kw_type]

        # Embed the description
        memory_embedding = self.get_observation_embedding(description)
        self.memory_embeddings[node_id] = memory_embedding

        # Check if this action was done by this agent
        self_is_actor = int(actor_id == self.agent_id)

        if memory_type == MemoryType.ACTION.value:
            new_memory = self.add_action(node_id,
                                         round,
                                         tick,
                                         description,
                                         location,
                                         success_status,
                                         memory_importance,
                                         type=MemoryType.ACTION,
                                         node_keywords=set(node_kwds),
                                         node_is_self=self_is_actor)
            
        if memory_type == MemoryType.DIALOGUE.value:
            pass
        if memory_type == MemoryType.REFLECTION.value:
            new_memory = self.add_reflection(node_id,
                                             round,
                                             tick,
                                             description,
                                             location,
                                             success_status,
                                             memory_importance,
                                             type=MemoryType.REFLECTION,
                                             node_keywords=set(node_kwds),
                                             node_is_self=self_is_actor)
        
        if memory_type == MemoryType.PERCEPT.value:
            new_memory = self.add_perception(node_id,
                                             round,
                                             tick,
                                             description,
                                             location,
                                             success_status,
                                             memory_importance,
                                             type=MemoryType.PERCEPT,
                                             node_keywords=set(node_kwds),
                                             node_is_self=self_is_actor)
        # Add node to sequential memory
        self.observations.append(new_memory)
        
        # NODE CACHEING
        # Cache the node under its keywords
        for category, kws_list in keywords.items():
            for word in kws_list:
                if word in self.keyword_nodes[category]:
                    self.keyword_nodes[category][word].append(node_id)
                else:
                    self.keyword_nodes[category].update({word: [node_id]})

        # Cache the node under the value of its MemoryType and its round ID.: 
        self.memory_type_nodes[memory_type].append(node_id)
        self.this_round_nodes[round].append(node_id)
        
        # increment the internal count of nodes
        self.num_observations += 1
            
    def add_action(self,
                   node_id,
                   round,
                   tick,
                   description,
                   location: str,
                   success_status: bool,
                   memory_importance: int,
                   type: MemoryType,
                   node_keywords: set,
                   node_is_self: int) -> None:
        
        new_action = ObservationNode(node_id,
                                     node_round=round,
                                     node_tick=tick,
                                     node_level=1,
                                     node_loc=location,
                                     node_description=description,
                                     node_success=success_status,
                                     embedding_key=node_id,
                                     node_importance=memory_importance,
                                     node_type=type,
                                     node_keywords=node_keywords,
                                     node_is_self=node_is_self)
        return new_action
    
    def add_reflection(self,
                       node_id,
                       round,
                       tick,
                       description,
                       location: str,
                       success_status: bool,
                       memory_importance: int,
                       type: MemoryType,
                       node_keywords: set,
                       node_is_self: int) -> None:
        
        new_reflection = ObservationNode(node_id,
                                         node_round=round,
                                         node_tick=tick,
                                         node_level=2,
                                         node_loc=location,
                                         node_description=description,
                                         node_success=success_status,
                                         embedding_key=node_id,
                                         node_importance=memory_importance,
                                         node_type=type,
                                         node_keywords=node_keywords,
                                         node_is_self=node_is_self)  
        return new_reflection
    
    def add_perception(self,
                       node_id,
                       round,
                       tick,
                       description,
                       location: str,
                       success_status: bool,
                       memory_importance: int,
                       type: MemoryType,
                       node_keywords: set,
                       node_is_self: int) -> None:

        new_perception = ObservationNode(node_id,
                                         node_round=round,
                                         node_tick=tick,
                                         node_level=1,
                                         node_loc=location,
                                         node_description=description,
                                         node_success=success_status,
                                         embedding_key=node_id,
                                         node_importance=memory_importance,
                                         node_type=type,
                                         node_keywords=node_keywords,
                                         node_is_self=node_is_self)
        return new_perception

    # ----------- GETTER METHODS -----------
    def get_observation(self, node_id):
        """
        Get the ith observation

        Args:
            node_id (int): the index of the requested ObservationNode

        Returns:
            ObservationNode: an ObservationNode
        """
        try:
            node = self.observations[node_id]
            return node
        except IndexError:
            return None
    
    def get_observation_description(self, node_id):
        node = self.get_observation(node_id)
        return node.node_description
    
    def get_observation_type(self, node_id):
        node = self.get_observation(node_id)
        return node.node_type
    
    def get_enumerated_description_list(self, 
                                        node_id_list, 
                                        as_type: Literal["str", "tuple"] = True
                                        ) -> Union[List[Tuple], List[str]]:
        """
        Args:
            node_id_list (_type_): _description_
            as_tuple (bool, optional): _description_. Defaults to True.

        Returns:
            _type_: _description_
        """
        enum_nodes = list(zip(node_id_list, [self.get_observation_description(i) for i in node_id_list]))
        if as_type == "tuple":
            return enum_nodes
        else:
            return [f"{mem_id}. {mem_desc}\n" for mem_id, mem_desc in enum_nodes]
    
    def get_observation_embedding(self, text):
        """
        Embed the text of an observation

        Args:
            text (str): the text to embed

        Returns:
            ndarray: an embedding vector
        """
        embedded_vector = get_text_embedding(text)
        return embedded_vector
    
    def get_observations_by_round(self, round):
        return self.this_round_nodes[round]
    
    def get_observations_by_type(self, obs_type):
        """
        Get a list of node_ids of a specified type

        Args:
            obs_type (int): a valid MemoryType value

        Returns:
            list: a list of nodes of type "obs_type"
        """
        if not self.is_valid_memory_type(obs_type):
            raise ValueError(f"{obs_type} is not a supported MemoryType({list(MemoryType)}).")
        
        if isinstance(obs_type, MemoryType):
            # Convert Enum to its value
            obs_type = obs_type.value
            
        return self.memory_type_nodes[obs_type]

    def get_most_recent_summary(self):
        nodes = self.observations[-self.lookback:]
        summary = f"The last {self.lookback} observations in chronological order you have made are:"
        for i, node in enumerate(nodes):
            summary += "\n{idx}. {desc}".format(idx=i, desc=node.node_description)
        return summary

    def get_embedding(self, index):
        """
        Get the index of a given node

        Args:
            index (int): index of the node

        Returns:
            np.array: an embedding of the node description
        """
        if self.node_exists(index):
            return self.memory_embeddings[index]
        
    def get_relationships_summary(self):
        raise NotImplementedError
    
    # ----------- SETTER METHODS -----------
    def set_embedding(self, node_id, new_embedding):
        """
        Update the embedding for an existing node

        Args:
            node_id (int): id of a memory
            new_embedding (np.ndarray): an embedding from OpenAI embeddings API
        """
        if not self.node_exists(node_id):
            return False
        else:
            self.memory_embeddings.update({node_id: new_embedding})
            return True
        
    def set_query_embeddings(self, character, round: int = 0):
        """
        Default "queries" for determining relevance when no explicit query has been passed to retrieve()

        Args:
            character (Character): agent of this memory
            round (int, optional): the round in the game. Defaults to 0.

        Returns:
            _type_: _description_
        """
        cached_queries = {}
        current_goal_embed = character.goals.get_goal_embedding(round=round)
        persona_embed = get_text_embedding(character.persona.summary)
        if persona_embed is not None:
            cached_queries["persona"] = persona_embed
        if current_goal_embed is not None:
            cached_queries["goals"] = current_goal_embed
        return cached_queries
    
    def set_goal_query(self, goal_embedding):
        try:
            self.query_embeddings.update({"goals": goal_embedding})
        except KeyError as e:
            print("Goal query embedding update failed. Skipping. Caught:\n", e)
    
    # ----------- UPDATE METHODS -----------
    def update_node(self, node_id, **kwargs) -> bool:
        try:
            node = self.get_observation(node_id)
        except IndexError:
            return False
        else:
            for k, v in kwargs.items():
                if hasattr(node, k):
                    setattr(node, k, v)
            return True
        
    def update_node_embedding(self, node_id, new_description) -> bool:
        """
        Update the embedding of a node

        Args:
            node_id (int): node id to switch
            new_description (str): the updated string description

        Returns:
            bool: success status
        """
        if not self.node_exists(node_id):
            return False
        else:
            updated_embedding = self.get_observation_embedding(new_description)
            success = self.set_embedding(node_id, updated_embedding)
            return success
    
    # ----------- MISC HELPER/VALIDATION METHODS -----------
    def replace_character(self, text, character_name, agent_descriptor):
        # Escape any special regex characters in the descriptor and character_name
        escaped_name = re.escape(character_name)
        escaped_descriptor = re.escape(" ".join([w for w in agent_descriptor.split() if w not in self.stopwords]))
        # Pattern to match 'the' optionally, then the descriptor optionally, followed by the character name
        # The descriptor and the character name can occur together or separately
        pattern = r'\b(?:the\s+)?(?:(?:{d}\s+)?{c}|{d})\b'.format(d=escaped_descriptor, c=escaped_name)
        replacement = 'you'
        return re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    def node_exists(self, node_id):
        return node_id < self.num_observations
    
    def is_valid_memory_type(self, memory_type):
        """
        Confirm that a memory type is valid.
        Allows for either the value or the name to be used as input

        Args:
            memory_type (MemoryType): the value to check

        Returns:
            bool: if test passed
        """
        if isinstance(memory_type, MemoryType):
            return True
        try:
            # Attempt to convert the input value to a MemoryType
            _ = MemoryType(memory_type) 
        except ValueError:
            return False
        else:
            return True
