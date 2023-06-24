# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_match_class.ipynb.

# %% auto 0
__all__ = ['convert_to_edge_name', 'is_anonymous_node', 'Match', 'mapping_to_match']

# %% ../nbs/02_match_class.ipynb 4
import networkx as nx
from networkx import DiGraph
from typing import *
from .core import _create_graph, _plot_graph, GraphRewriteException, NodeName, EdgeName

# %% ../nbs/02_match_class.ipynb 11
def convert_to_edge_name(src: NodeName, dest: NodeName) -> str:
    """Given a pair of node names, source and destination, return the name of the edge
    connecting the two in the format {src}->{dest}, which is the same format the parser
    uses to create edges in the pattern graph.

    Args:
        src (NodeName): A node name
        dest (NodeName): A node name

    Returns:
        str: A representative name for the edge (src, dest).
    """
    return f"{src}->{dest}"

# %% ../nbs/02_match_class.ipynb 13
def is_anonymous_node(node_name: NodeName) -> bool:
    """Given a name of a node in the pattern graph, return true if it begins with '$',
    which is the notion the parser uses to denote anonymous nodes.

    Args:
        node_name (NodeName): A node name in the pattern

    Returns:
        bool: Returns True if the node is anonymous, False otherwise.
    """
    return len(node_name) >= 1 and node_name[0] == '$'

# %% ../nbs/02_match_class.ipynb 16
class Match:
    """Represents a single match of a pattern inside an input graph.
     Provides a subview to a graph, limited to the nodes, edges and attributes specified in the pattern.
    """
    def __init__(self, graph: DiGraph, nodes: List[NodeName], edges: List[EdgeName], mapping: Dict[NodeName, NodeName]):
        self.graph: DiGraph = graph
        self.__nodes: List[NodeName] = nodes
        self.__edges: List[EdgeName] = edges
        self.mapping: Dict[NodeName, NodeName] = mapping

    def __get_node(self, pattern_node):
        return self.graph.nodes[self.mapping[pattern_node]]

    def __get_edge(self, pattern_src, pattern_dst):
        if (pattern_src, pattern_dst) not in self.__edges:
            raise GraphRewriteException("Edge does not exist in the pattern")
        return self.graph.edges[self.mapping[pattern_src], self.mapping[pattern_dst]]

    def nodes(self):
        return {pattern_node: self.__get_node(pattern_node) for pattern_node in self.__nodes}

    def edges(self):
        return {convert_to_edge_name(pattern_src, pattern_dest): self.__get_edge(pattern_src, pattern_dest) for (pattern_src, pattern_dest) in self.__edges}

    def __getitem__(self, key: Union[NodeName, str]):
        """Returns the node / edge of the input graph, which was mapped by the key in the pattern during matching.

        Args:
            key (Union[NodeName, str]): A symbolic name used by the pattern (for a node / edge)

        Raises:
            GraphRewriteException: If the key doesn't exist in the pattern, or is mapped to a node / edge
            which does not exist anymore (due to removal by the transformation, for example).

        Returns:
            The corresponding node / edge of the input graph
        """
        try:
            if str(key).__contains__("->") and len(str(key).split("->")) == 2:
                end_nodes = str(key).split("->")
                return self.__get_edge(end_nodes[0], end_nodes[1])
            else:
                return self.__get_node(key)
        except:
            raise GraphRewriteException("The symbol does not exist in the pattern, or it was removed from the graph")

# %% ../nbs/02_match_class.ipynb 18
def mapping_to_match(input: DiGraph, pattern: DiGraph, mapping: Dict[NodeName, NodeName]) -> Match:
    """Given a mapping, which denotes a match of the pattern in the input graph,
    create a corresponding instance of the Match class.

    Args:
        input (DiGraph): An input graph
        pattern (DiGraph): A pattern graph
        mapping (Dict[NodeName, NodeName]): A mapping from nodes in the pattern graph to nodes in the input graph, 
        that denotes a single match between the two.

    Returns:
        Match: A corresponding instance of the Match class
    """
    nodes_list, edges_list = [], []
    cleared_mapping = mapping.copy()

    for pattern_node in mapping.keys():
        if is_anonymous_node(pattern_node):
            cleared_mapping.pop(pattern_node)
            continue # as we don't want to include this node in the Match
        nodes_list.append(pattern_node)

    for (n1, n2) in pattern.edges:
        if is_anonymous_node(n1) or is_anonymous_node(n2):
            continue # as before
        edges_list.append((n1, n2))

    return Match(input, nodes_list, edges_list, cleared_mapping)
