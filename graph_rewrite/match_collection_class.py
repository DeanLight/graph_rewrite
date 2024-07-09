# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/07_match_collection_class.ipynb.

# %% auto 0
__all__ = ['ItemName', 'CollectionType', 'MatchCollection']

# %% ../nbs/07_match_collection_class.ipynb 3
# Collections Feature

import networkx as nx
from networkx import DiGraph
from typing import *
from .core import _create_graph, draw, GraphRewriteException, NodeName, EdgeName
from enum import Enum

# %% ../nbs/07_match_collection_class.ipynb 4
# Collections Feature

# Define the Enum for CollectionType
class CollectionType(Enum):
    EDGES = "edges"
    NODES = "nodes"

# %% ../nbs/07_match_collection_class.ipynb 5
# Collections Feature

# Define ItemName type which could be a DiGraph node or edge
ItemName = Union[NodeName, EdgeName]

# %% ../nbs/07_match_collection_class.ipynb 6
# Collections Feature

class MatchCollection:
    def __init__(self, graph: DiGraph, CollectionName: str, type: CollectionType, items: List[ItemName], mapping={}):
        self.graph = graph
        self.CollectionName: str = CollectionName
        self.type: CollectionType = type
        self.items: List[ItemName] = items
        self.mapping: Dict[ItemName, ItemName] = mapping

    def __getitem__(self, attribute_name: str):
        """Returns a list of attributes from items in the collection.

        Args:
            attribute_name (str): The name of the attribute to retrieve from each item.

        Returns:
            List: A list of attribute values from the items.
        
        return [getattr(item, attribute_name) for item in self.items]
        """
        
        pass

    def add_item(self, ItemName, graphItemName):
        self.items.append(ItemName)
        self.mapping[ItemName] = graphItemName

    #TODO: add support for iterator over the items and/or a getter function for items if needed