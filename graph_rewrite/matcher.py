# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_matcher.ipynb.

# %% auto 0
__all__ = ['FilterFunc', 'Constant', 'find_intersecting_nodes', 'find_collection_matches', 'find_matches']

# %% ../nbs/03_matcher.ipynb 4
from itertools import product, permutations
from typing import Tuple, Iterator

# %% ../nbs/03_matcher.ipynb 7
from typing import *
from networkx import DiGraph
from networkx.algorithms import isomorphism # check subgraph's isom.
import itertools # iterating over all nodes\edges combinations

from .core import NodeName, _create_graph, draw
from .lhs import lhs_to_graph
from .match_class import Match, mapping_to_match, is_anonymous_node,draw_match

# %% ../nbs/03_matcher.ipynb 10
# TODO: Ensure we separate between constant attributes and existence checks (constants).
# a[id] -> existence check (can be checked before combinatorics)
# a[id=Constant(3)] -> constant value check (can be checked before combinatorics)

# TODO: Email Dean regarding the parser ability to support constant values in the pattern graph - it is currently not supported, and so all constant values will still
#  result in a None value in the pattern graph.

# This class is used to represent a constant value in the pattern graph (e.g., a[id=3]).
# It helps differentiate between constant values and values that are dependent on runtime (e.g., when using conditions while creating the LHS).
class Constant:
    def __init__(self, value):
        self.value = value

# Helper function to compare pattern attributes (node or edge) with input attributes
def _attributes_match(pattern_attrs: dict, input_attrs: dict) -> bool:
    """
    Check if the input attributes match the pattern attributes.

    This function supports both:
    - Existence checks (ensures that required attributes exist).
    - Constant value checks (ensures that constant values match).

    Args:
        pattern_attrs (dict): Attributes of the pattern (node or edge).
        input_attrs (dict): Attributes of the input (node or edge).

    Returns:
        bool: True if the input attributes match the pattern attributes, False otherwise.
    """
    for attr_name, attr_value in pattern_attrs.items():
        if attr_name not in input_attrs:  # If the attribute does not exist, return False
            return False
        
        if attr_value is None: # If the attribute exists, but the value is None, continue to the next attribute
            continue

        # TODO: This is not supported yet due to the parser not supporting constant values in the pattern graph - we will never reach this point, and it is implemented for future use, once the parser supports it.
        if isinstance(attr_value, Constant):  # If the attribute exists, and the value is a constant, check if the value matches
            if input_attrs[attr_name] != attr_value.value:
                return False

    return True

# %% ../nbs/03_matcher.ipynb 12
def _filter_candidates_by_edges(pattern: DiGraph, input_graph: DiGraph, pattern_node: NodeName, candidate_input_nodes: Set[NodeName]) -> Set[NodeName]:
    """
    Helper function for _find_input_nodes_with_pattern_attributes_and_edges.
    Further filters the candidate input nodes by checking if their edges match the pattern node's edges by attributes.
    The function first collects all edges of the pattern node that have attributes specified and then filters out
    the candidates that don't have at least one unique matching edge for each pattern edge.

    Args:
        pattern (DiGraph): The pattern graph.
        input_graph (DiGraph): The input graph.
        pattern_node (NodeName): The pattern node.
        candidate_input_nodes (Set[NodeName]): A set of candidate input nodes that already match the node attributes.

    Returns:
        Set[NodeName]: A filtered set of candidate input nodes that also have matching unique edges.
    """
    pattern_edges_with_attrs = [
        (pattern_node, pattern_neighbor, pattern.get_edge_data(pattern_node, pattern_neighbor))
        for pattern_neighbor in pattern.neighbors(pattern_node)
        if pattern.get_edge_data(pattern_node, pattern_neighbor)  # Only edges with attributes
    ]

    if not pattern_edges_with_attrs:
        return candidate_input_nodes

    filtered_candidates = set()

    for input_node in candidate_input_nodes:
        unused_input_edges = {(input_node, input_neighbor) for input_neighbor in input_graph.neighbors(input_node)}

        valid_candidate = True  # Assume valid unless proven otherwise

        for _, _, pattern_edge_attrs in pattern_edges_with_attrs:
            match_found = False

            for input_edge in list(unused_input_edges):
                input_edge_attrs = input_graph.get_edge_data(*input_edge, default={})

                if _attributes_match(pattern_edge_attrs, input_edge_attrs):
                    unused_input_edges.remove(input_edge)
                    match_found = True
                    break

            if not match_found:
                valid_candidate = False
                break

        if valid_candidate:
            filtered_candidates.add(input_node)

    return filtered_candidates

# %% ../nbs/03_matcher.ipynb 13
def _find_input_nodes_candidates_for_pattern_node(pattern_node: NodeName, pattern: DiGraph, input_graph: DiGraph) -> set[NodeName]:
    """
    Given a pattern node and an input graph, return a set of input graph nodes that:
    - Contain the required attributes of the pattern node, including constant value checks (if specified) and existence checks (if no value is specified / no constant value).
    - Have at least one edge with matching attributes for each edge of the pattern node that has attributes specified.

    Args:
        pattern_node (NodeName): The pattern node.
        pattern (DiGraph): The pattern graph.
        input_graph (DiGraph): The input graph.

    Returns:
        set[NodeName]: A set of input graph nodes that match the required attributes and have at least one matching edge.
    """

    pattern_node_attrs = pattern.nodes[pattern_node]

    if "_id" in pattern_node_attrs: #TODO: understand why this is here (_id)
        input_node_id = pattern_node_attrs.pop("_id")
        input_nodes_to_check = [input_node_id]
    else:
        input_nodes_to_check = list(input_graph.nodes)

    # Filter nodes by attributes first
    candidate_nodes = {
        input_node
        for input_node in input_nodes_to_check
        if _attributes_match(pattern_node_attrs, input_graph.nodes[input_node])
    }

    # Further filter candidate nodes by checking if they have matching edges
    return _filter_candidates_by_edges(pattern, input_graph, pattern_node, candidate_nodes)

# %% ../nbs/03_matcher.ipynb 15
# TODO: maybe we should change the name of this function to something more descriptive, that includes attributes
def _find_structural_matches(graph: DiGraph, pattern: DiGraph) -> Iterator[Tuple[DiGraph, Dict[NodeName, NodeName]]]:
    """
    Find all subgraphs in the input graph that match the given pattern graph based on both structure (nodes and edges)
    and attributes (existence of attributes or constant value checks).

    A subgraph is considered isomorphic if it has the same structure (nodes and edges) as the pattern graph
    and the attributes of the nodes and edges match the specified attributes in the pattern graph.

    Args:
        graph (DiGraph): The graph to search for matches.
        pattern (DiGraph): The pattern graph representing the structure and attributes to match.

    Yields:
        Iterator[Tuple[DiGraph, Dict[NodeName, NodeName]]]: Tuples of (subgraph, mapping),
        where subgraph is the matched subgraph, and mapping is a dictionary mapping nodes in the
        subgraph to nodes in the pattern.
    """
    p_nodes = list(pattern.nodes)
    p_edges = list(pattern.edges)

    pattern_to_input_nodes_candidates = {
        pattern_node: _find_input_nodes_candidates_for_pattern_node(pattern_node, pattern, graph)
        for pattern_node in p_nodes
    }

    # All valid combinations of candidate node assignments (combinations won't work here since we want to ensure each pattern node is mapped to a unique input node)
    candidate_assignments = product(
        *(pattern_to_input_nodes_candidates[pattern_node] for pattern_node in p_nodes)
    )

    # Find isomorphic subgraphs
    for assignment in candidate_assignments:
        if len(set(assignment)) != len(assignment): # Ensure all input nodes are unique
            continue

        nodes_assignment_mapping = dict(zip(p_nodes, assignment))

        subgraph = DiGraph()
        subgraph.add_nodes_from(assignment)

        # Validate edges based on node mapping
        for pattern_src, pattern_dst in p_edges:
            input_src, input_dst = nodes_assignment_mapping[pattern_src], nodes_assignment_mapping[pattern_dst]

            if (input_src, input_dst) in graph.edges and _attributes_match(
                pattern.get_edge_data(pattern_src, pattern_dst, default={}),
                graph.get_edge_data(input_src, input_dst, default={})
            ):
                subgraph.add_edge(input_src, input_dst)
            else:
                # If the edge does not match, skip this candidate
                break
        else:
            # If all edges are validated, check the isomorphism
            if len(subgraph.edges) == len(p_edges) and isomorphism.is_isomorphic(subgraph, pattern):
                yield subgraph, nodes_assignment_mapping

#OLD    
'''
    # We find all possible candidates for each node in the pattern, by checking the attributes of the nodes in the graph
    pattern_to_input_candidates = {pattern_node: _find_input_nodes_with_pattern_attributes(pattern.nodes[pattern_node], graph) for pattern_node in pattern.nodes}
    candidate_assignments = itertools.product(*(pattern_to_input_candidates[pattern_node] for pattern_node in list(pattern.nodes)))
    for assignment in candidate_assignments:
        # Make sure the sub_nodes are unique - we don't want to have multiple nodes in the subgraph that are mapped to the same node in the pattern
        if len(set(assignment)) != len(assignment): 
            continue
        assignment_mapping = dict(zip(list(pattern.nodes), assignment))
        subg = DiGraph()
        subg.add_nodes_from(list(assignment))
        for pattern_edge in list(pattern.edges):
            graph_edge = (assignment_mapping[pattern_edge[0]], assignment_mapping[pattern_edge[1]])
            if graph_edge in graph.edges and _input_node_has_pattern_node_attributes(graph.edges[graph_edge], pattern.edges[edge]):
              subg.add_edge(graph_edge[0], graph_edge[1])
            else: # In that case we don't need to check the rest of the isomorphism
                break
                             
        # We only yield mappings for subgraphs that have the same amount of edges as the pattern - otherwise the subgraph won't be an isomorphism
        if len(subg.edges) == len(pattern.edges):
            yield assignment_mapping
'''


# %% ../nbs/03_matcher.ipynb 17
FilterFunc = Callable[[Match], bool]

# %% ../nbs/03_matcher.ipynb 20
def _filter_duplicated_matches(matches: list[Match]) -> Iterator[Match]:
    """Remove duplicates from a list of Matches, based on their mappings. Return an iterator of the matches without duplications.

    Args:
        matches (list[Match]): list of Match objects

    Yields:
        Iterator[list[Match]]: Iterator of the matches without duplications.
    """

    yield from set(matches)
    # TODO: optimization - using set involves instantiation of all matches, check if we can avoid it

# OLD
'''
    new_list = []
    for match in matches:
        if match not in new_list:
            new_list.append(match)
            yield match
'''



# %% ../nbs/03_matcher.ipynb 21
# Finds 
def find_intersecting_nodes(match: dict, collection_pattern: DiGraph) -> set:
    # Step 1: Extract all node names from self._nodes and the node collections (if they do not exist yet, they will be empty - no harm is done).
    # Step 2: Find all nodes with the same name in collection_pattern - these are the intersecting nodes.
    # Step 3: Return all matching node names.
    if collection_pattern is None:
        return set()
    collection_nodes = set(collection_pattern.nodes)
    match_nodes = set(match.keys())
    return collection_nodes & match_nodes

# This function is used to find all the collections that match the pattern, by comparing the intersected nodes
def find_collection_matches(input_graph: DiGraph, collecions_pattern: DiGraph, intersected_nodes_matches: List):
    g_id = input_graph.copy()
    for mapping, intersected_nodes in intersected_nodes_matches:
        pattern_id = collecions_pattern.copy()
        for node in intersected_nodes:
            pattern_id.nodes[node]['_id'] = mapping[node]

        # Find all structural matches (isomorphisms)
        attribute_matches =  [match for match in _find_structural_matches(g_id, pattern_id)]
        # Find matches with attributes among isoms (match pattern's attributes)
        #attribute_matches = [mapping for (subgraph, mapping) in isom_matches if _does_isom_match_pattern((subgraph, mapping), pattern_id)]

        # Create one mapping for the collections out of attribute_matches
        collections_mapping = {}
        for d in attribute_matches:
            for collectionName, value in d.items():
                if collectionName in intersected_nodes:
                    continue
                if collectionName not in collections_mapping:
                    collections_mapping[collectionName] = set()
                collections_mapping[collectionName].add(value)
        if collecions_pattern.number_of_nodes() == 0 or collections_mapping != {}:
            yield mapping, collections_mapping



# %% ../nbs/03_matcher.ipynb 23
# Dean's suggestion: make sure there are no "duplicated mappings" of different node names to the same node - make sure there is no case where
# one is deleted and the other is not
# This also should be done for attributes
# Check how regraph does it, and if there is no such thing, check the mathematically correct way to do it
def find_matches(input_graph: DiGraph, pattern: DiGraph, collections_pattern: DiGraph = None, condition: FilterFunc = lambda match: True) -> Match:
    """Find all matches of a pattern graph in an input graph, for which a certain condition holds.
    That is, subgraphs of the input graph which have the same nodes, edges, attributes and required attribute values
    as the pattern defines, which satisfy any additional condition the user defined.

    Args:
        input_graph (DiGraph): A graph to find matches in
        pattern (DiGraph): A pattern graph produced by the LHS Parser.
        condition (FilterFunc, optional): A function which recives a Match objects, and checks whether some condition holds
            for the corresponding match. Defaults to a condition function which always returns True.

    Yields:
        Iterator[Match]: Iterator of Match objects (without duplications), each corresponds to a match of the pattern in the input graph.
    """

    # Narrow down search space by keeping only input-graph nodes that have any attribute in common as some pattern node
    # And reduce the input graph to the matching nodes + connected edges
    matching_nodes = [n for (n, attrs) in input_graph.nodes(data=True) if _does_node_match_pattern(attrs, pattern)]
    reduced_input_g = input_graph.subgraph(matching_nodes).copy()    

    # Remove all edges that are not between matching nodes or do not match the pattern by their attributes from the reduced graph
    reduced_input_g.remove_edges_from([edge for edge in reduced_input_g.edges if not _does_edge_match_pattern(reduced_input_g.edges[edge], pattern)])
        
    # Find all structural matches (isomorphisms), including attributes
    attribute_matches =  [match for match in _find_structural_matches(reduced_input_g, pattern)]

    # Find all collections that match the pattern
    if collections_pattern is not None:
        intersected_nodes_matches = [(mapping, find_intersecting_nodes(mapping, collections_pattern)) for mapping in attribute_matches]
        collection_matches = [(mapping, collections_mapping) for mapping, collections_mapping in 
                            find_collection_matches(reduced_input_g, collections_pattern, intersected_nodes_matches)]
    else:
        collection_matches = [(mapping, dict()) for mapping in attribute_matches]

    # construct a list of Match objects. Note that the condition is checked on a Match that includes anonymous nodes (as it might use it)
    # but the Match that we return does not include the anonymous parts.
    # Therefore, we first construct a list of tuples - the first is the mapping with anonymous, the second isn't
    matches_list = [(mapping_to_match(input_graph, pattern, collections_pattern, mapping, collection_mapping, filter=False),
                      mapping_to_match(input_graph, pattern, collections_pattern, mapping, collection_mapping)) 
                    for mapping, collection_mapping in collection_matches]
    # Then filter the list, to contain only the filtered match whose unfiltered version matches the condition
    filtered_matches =  [filtered_match for (unfiltered_match, filtered_match) in matches_list if condition(unfiltered_match)]
    # And finally, remove duplicates (might be created because we removed the anonymous nodes)
    yield from _remove_duplicated_matches(filtered_matches)



