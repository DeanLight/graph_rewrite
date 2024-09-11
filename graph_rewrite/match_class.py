# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_match_class.ipynb.

# %% auto 0
__all__ = ['convert_to_edge_name', 'is_anonymous_node', 'NodeType', 'NodeAttributeAccessor', 'EdgeAttributeAccessor', 'Match',
           'mapping_to_match']

# %% ../nbs/02_match_class.ipynb 6
import networkx as nx
from networkx import DiGraph
from typing import *
from .core import _create_graph, draw, GraphRewriteException, NodeName, EdgeName

# %% ../nbs/02_match_class.ipynb 13
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

# %% ../nbs/02_match_class.ipynb 15
def is_anonymous_node(node_name: NodeName) -> bool:
    """Given a name of a node in the pattern graph, return true if it begins with '$',
    which is the notion the parser uses to denote anonymous nodes.

    Args:
        node_name (NodeName): A node name in the pattern

    Returns:
        bool: Returns True if the node is anonymous, False otherwise.
    """
    return len(node_name) >= 1 and node_name[0] == '_'

# %% ../nbs/02_match_class.ipynb 16
'''
Classes that are used by Match class
'''

class NodeType(Enum):
    """Enum of the different types of nodes in the pattern graph.
    """
    SINGLE = 1
    COLLECTION = 2

'''
Classes for accessing attributes of nodes and edges in a collection.
If when using the __getitem__ method of the Match class, the result is a collection of nodes or edges,
the corresponding NodeAttributeAccessor or EdgeAttributeAccessor class is returned, respectively.
When using the __getitem__ method of these classes, a list of the requested attribute from each node or edge in the collection is returned.
'''
class NodeAttributeAccessor:
    """
    This class acts as a wrapper for a set of nodes, allowing access to specific attributes.
    """
    def __init__(self, nodes):
        self.nodes = nodes

    def __getitem__(self, attribute):
        # Return a list of the requested attribute from each node in the set
        return [getattr(node, attribute) for node in self.nodes if hasattr(node, attribute)]

class EdgeAttributeAccessor:
    """
    This class acts as a wrapper for a set of edges, allowing access to specific attributes.
    """
    def __init__(self, edges):
        self.edges = edges

    def __getitem__(self, attribute):
        # Return a list of the requested attribute from each edge in the set
        return [getattr(edge, attribute) for edge in self.edges if hasattr(edge, attribute)]

# %% ../nbs/02_match_class.ipynb 19
class Match:
    """Represents a single match of a pattern inside an input graph.
     Provides a subview to a graph, limited to the nodes, edges and attributes specified in the pattern.
    """
    def __init__(self, graph: DiGraph, nodes: List[NodeName], edges: List[EdgeName], 
                 mapping: Dict[NodeName, Set[NodeName]], node_type_mapping: Dict[NodeName, NodeType]):
        self.graph: DiGraph = graph
        self._nodes: List[NodeName] = nodes
        self._edges: List[EdgeName] = edges
        self.mapping: Dict[NodeName, Set[NodeName]] = mapping # Node names and edges can represent either single nodes or collections of nodes, so for each node name is mapped to a set of input nodes:
        self.node_type_mapping: Dict[NodeName, NodeType] = node_type_mapping  # A dictionary that maps each node name to its type (single or collection)
    
    # A function that checks if the node is valid and raises an exception if it is not
    def check_node_in_pattern(self, pattern_node: NodeName):
        if not pattern_node in self._nodes:
            raise GraphRewriteException(f"Node {pattern_node} does not exist in the pattern")
        
    # A function that checks if the edge is valid and raises an exception if it is not
    def check_edge_in_pattern(self, pattern_src: NodeName, pattern_dst: NodeName):
        if not (pattern_src, pattern_dst) in self._edges:
            raise GraphRewriteException(f"Edge {(pattern_src, pattern_dst)} does not exist in the pattern")
        
             
    # Two boolean functions that checks if the pattern node is a single node or a collection of nodes
    def is_collection(self, pattern_node: NodeName) -> bool:
        return self.node_type_mapping[pattern_node] == NodeType.COLLECTION

    def is_single(self, pattern_node: NodeName) -> bool:
        return self.node_type_mapping[pattern_node] == NodeType.SINGLE
    
    # Returns the node or the collection of nodes mapped to the pattern node
    # If the node is a single node, we return the single node that is mapped to it, otherwise we return a set of nodes
    def __get_node(self, pattern_node):
        self.check_node_in_pattern(pattern_node)
        if self.is_single(pattern_node):
            return self.graph.nodes[list(self.mapping[pattern_node])[0]]
        else:
            return [self.graph.nodes[node] for node in self.mapping[pattern_node]]
    
    # Returns the edge or the collection of edges mapped to the pattern edge
    # If the edge is between two single nodes, we return the edge itself, otherwise we return a set of edges
    def __get_edge(self, pattern_src, pattern_dst):
        self.check_edge_in_pattern(pattern_src, pattern_dst)
        src = self.mapping[pattern_src]
        dst = self.mapping[pattern_dst]
        if self.is_single(pattern_src) and self.is_single(pattern_dst):
            src_single = list(src)[0]
            dst_single = list(dst)[0]
            return self.graph.edges[src_single, dst_single]
        else:
            return [self.graph.edges[src, dst] for src in src for dst in dst]
    
    def nodes(self):
        return {pattern_node: self.__get_node(pattern_node) for pattern_node in self._nodes}        
    
    def edges(self):
        return {convert_to_edge_name(pattern_src, pattern_dest): self.__get_edge(pattern_src, pattern_dest) for (pattern_src, pattern_dest) in self._edges}

    def set_graph(self, graph: DiGraph):
        self.graph = graph

    def __eq__(self, other):
        if type(other) is Match and len(other.mapping.items()) == len(self.mapping.items()):
            return all([other.mapping.get(k) == v for k,v in self.mapping.items()])
        return False

    def __getitem__(self, key: Union[NodeName, str]):
        """
        Returns the node/edge (single or collections) of the input graph, which was mapped by the key in the pattern during matching.
        Supports nested access when the result is a set of nodes or edges (i.e. a collection).

        Args:
            key (Union[NodeName, str]): A symbolic name used by the pattern (for a node / edge)

        Raises:
            GraphRewriteException: If the key doesn't exist in the pattern, or is mapped to a node/edge
            which does not exist anymore (due to removal by the transformation, for example).

        Returns:
            The corresponding node/edge of the input graph, or a list of 'name' attributes if requested.
            If the result is a set of nodes or edges (if it is a collection), returns a NodeAttributeAccessor or EdgeAttributeAccessor respectively, 
            to allow access to specific attributes of each node/edge in the collection.
        """
        try:
            # Check if the key is for an edge ("node1->node2")
            if str(key).__contains__("->") and len(str(key).split("->")) == 2:
                end_nodes = str(key).split("->")
                edge_or_edges = self.__get_edge(end_nodes[0], end_nodes[1])
                
                # If it's a set of edges, return an EdgeAttributeAccessor, that creates a list of attributes for each edge in the set
                if self.is_collection(end_nodes[0]) or self.is_collection(end_nodes[1]):
                    return EdgeAttributeAccessor(edge_or_edges)
                else: # Single edge
                    return edge_or_edges
            
            # Otherwise, assume it's for a node
            node_or_nodes = self.__get_node(key)
            
            # If the result is a set of nodes, return a NodeAttributeAccessor, that creates a list of attributes for each node in the set
            if self.is_collection(key):
                return NodeAttributeAccessor(node_or_nodes)
            else: # Single node
                return node_or_nodes
        except:
            raise GraphRewriteException(f"The symbol {key} does not exist in the pattern, or it was removed from the graph")
        
    def __str__(self):
        return self.mapping.__str__()

# %% ../nbs/02_match_class.ipynb 21
def mapping_to_match(input: DiGraph, pattern: DiGraph, collections_pattern: DiGraph, mapping: Dict[NodeName, Set[NodeName]],
                      node_type_mapping: Dict[NodeName,NodeType], filter: bool=True) -> Match:
    """Given a mapping, which denotes a match of the pattern in the input graph,
    create a corresponding instance of the Match class.

    Args:
        input (DiGraph): An input graph
        pattern (DiGraph): A pattern graph
        mapping (Dict[NodeName, Set[NodeName]]): A mapping of nodes in the pattern to nodes in the input graph
        node_type_mapping (Dict[NodeName, NodeType]): A mapping of nodes in the pattern to their type (single or collection)
        filter (bool): If True, filter out anonymous nodes from the match

    Returns:
        Match: A corresponding instance of the Match class
    """
    nodes_list = []
    edges_list = []

    cleared_mapping = mapping.copy()

    for pattern_node in mapping.keys():
        if filter and is_anonymous_node(pattern_node):
            cleared_mapping.pop(pattern_node)
            continue # as we don't want to include this node in the Match
        nodes_list.append(pattern_node)

    for (n1, n2) in pattern.edges:
        if filter and (is_anonymous_node(n1) or is_anonymous_node(n2)):
            continue # as before
        edges_list.append((n1, n2))

    return Match(input, nodes_list, edges_list, cleared_mapping, node_type_mapping)
