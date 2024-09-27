# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_matcher.ipynb.

# %% auto 0
__all__ = ['FilterFunc', 'Constant']

# %% ../nbs/03_matcher.ipynb 6
from typing import *
from networkx import DiGraph
from networkx.algorithms import isomorphism # check subgraph's isom.
from .core import NodeName, _create_graph, draw
from .lhs import lhs_to_graph
from .match_class import Match, mapping_to_match, is_anonymous_node,draw_match
from itertools import product, permutations
from typing import Tuple, Iterator

# %% ../nbs/03_matcher.ipynb 9
# TODO: Ensure we separate between constant attributes and existence checks (constants).
# a[id] -> existence check (can be checked before combinatorics)
# a[id=Constant(3)] -> constant value check (can be checked before combinatorics)

# TODO: Email Dean regarding the parser ability to support constant values in the pattern graph - it is currently not supported, and so all constant values will still
#  result in a None value in the pattern graph.
class Constant:
    def __init__(self, value):
        self.value = value


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

        # TODO: This is not supported yet due to the parser not supporting constant values in the pattern graph - we will never reach this point, and it is implemented for future use, 
        # once the parser supports it.
        if isinstance(attr_value, Constant):  # If the attribute exists, and the value is a constant, check if the value matches
            if input_attrs[attr_name] != attr_value.value:
                return False

    return True

# %% ../nbs/03_matcher.ipynb 11
def _find_input_nodes_candidates(pattern_node: NodeName, pattern: DiGraph, input_graph: DiGraph) -> set[NodeName]:
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

    return candidate_nodes

# %% ../nbs/03_matcher.ipynb 12
def _filter_edge_candidates(input_graph: DiGraph, pattern: DiGraph, src_pattern_node: NodeName, dst_pattern_node: NodeName, 
                               src_candidates: Set[NodeName], dst_candidates: Set[NodeName]) -> Set[Tuple[NodeName, NodeName]]:
    """
    Filter the input node candidates for two pattern nodes by checking if the edges between them in the input graph exist
    and match the pattern edge attributes.

    This function reduces the number of candidate pairs before generating assignments in _find_pattern_based_matches.

    Args:
        input_graph (DiGraph): The input graph.
        pattern (DiGraph): The pattern graph (provides the edge attributes).
        src_pattern_node (NodeName): The source pattern node.
        dst_pattern_node (NodeName): The destination pattern node.
        src_candidates (Set[NodeName]): Current candidates for the source pattern node.
        dst_candidates (Set[NodeName]): Current candidates for the destination pattern node.

    Returns:
        Set[Tuple[NodeName, NodeName]]: A set of valid candidate edge assignments (source, destination).
    """
    pattern_edge_attrs = pattern.get_edge_data(src_pattern_node, dst_pattern_node, default={})

    # Filter input edge candidates for the pattern edge by checking if the input edge exists and matches the pattern edge attributes (if specified)
    valid_edge_candidates = {
        (src_candidate, dst_candidate)
        for src_candidate, dst_candidate in product(src_candidates, dst_candidates)
        if (src_candidate, dst_candidate) in input_graph.edges and
           _attributes_match(pattern_edge_attrs, input_graph.get_edge_data(src_candidate, dst_candidate, default={})) and
           ((src_pattern_node==dst_pattern_node and src_candidate==dst_candidate) or src_pattern_node!=dst_pattern_node) 
    }

    return valid_edge_candidates

# %% ../nbs/03_matcher.ipynb 14
def _add_candidates_to_assignment(src_candidate: NodeName, dst_candidate: NodeName, partial_assignment: Dict[NodeName, NodeName], 
                                  src_pattern_node: NodeName, dst_pattern_node: NodeName) -> Optional[Dict[NodeName, NodeName]]:
    """
    Helper function to handle the case of adding src and dst candidates to the partial assignment
    based on different conditions (both unassigned, one already assigned correctly, etc.).

    Args:
        src_candidate: The candidate for the source pattern node.
        dst_candidate: The candidate for the destination pattern node.
        partial_assignment: The current partial assignment being considered.
        src_pattern_node: The source pattern node.
        dst_pattern_node: The destination pattern node.

    Returns:
        A dictionary representing the new assignment if valid, or None if it doesn't apply.
    """
    # Copy the partial assignment to avoid modifying the original
    new_assignment = {pattern_node : input_node for pattern_node, input_node in partial_assignment.items()}

    src_assigned = src_candidate in partial_assignment.values()
    dst_assigned = dst_candidate in partial_assignment.values()

    # Case 1: Neither src nor dst are assigned, add both
    if not src_assigned and not dst_assigned:
        new_assignment[src_pattern_node] = src_candidate
        new_assignment[dst_pattern_node] = dst_candidate
        return new_assignment

    # Case 2: src is already correctly assigned, add dst
    elif src_assigned and partial_assignment.get(src_pattern_node) == src_candidate and not dst_assigned:
        new_assignment[dst_pattern_node] = dst_candidate
        return new_assignment

    # Case 3: dst is already correctly assigned, add src
    elif dst_assigned and partial_assignment.get(dst_pattern_node) == dst_candidate and not src_assigned:
        new_assignment[src_pattern_node] = src_candidate
        return new_assignment
    
    # Case 4: src and dst are the same, and the edge is a self-loop
    elif src_assigned and dst_assigned and partial_assignment.get(src_pattern_node) == src_candidate and partial_assignment.get(dst_pattern_node) == dst_candidate:
        return new_assignment

    return None  # No valid assignment if none of the cases match


# %% ../nbs/03_matcher.ipynb 15
def _find_pattern_based_matches(graph: DiGraph, pattern: DiGraph) -> Iterator[Tuple[DiGraph, Dict[NodeName, NodeName]]]:
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

    # For pattern edges, gather valid edge candidates (pairs of nodes with matching attributes)
    edge_candidates = {}
    for src_pattern_node, dst_pattern_node in pattern.edges:
        src_candidates = _find_input_nodes_candidates(src_pattern_node, pattern, graph)
        dst_candidates = _find_input_nodes_candidates(dst_pattern_node, pattern, graph)
        edge_candidates[(src_pattern_node, dst_pattern_node)] = _filter_edge_candidates(
            graph, pattern, src_pattern_node, dst_pattern_node, src_candidates, dst_candidates)
        
    #STAVS DEBUG
    print("Edge candidates: ", edge_candidates)


    # Initialize partial assignments based on valid edge candidates
    # We can't use set because dict is not hashable, so we use a list
    partial_assignments = list()

    for (src_pattern_node, dst_pattern_node) in pattern.edges:
        new_assignments = list()

        valid_edge_candidates = edge_candidates[(src_pattern_node, dst_pattern_node)]
        for src_candidate, dst_candidate in valid_edge_candidates:
            for partial_assignment in partial_assignments or [{}]:
                new_assignment = {pattern_node : input_node for pattern_node, input_node in partial_assignment.items()}
                new_assignment = _add_candidates_to_assignment(src_candidate, dst_candidate, partial_assignment, src_pattern_node, dst_pattern_node)
                if new_assignment is not None:
                    new_assignments.append(new_assignment)
                    
        if not new_assignments:  # If no new assignments are found for a pair of pattern nodes, the pattern cannot be matched
             return
        partial_assignments = new_assignments

    #STAVS DEBUG
    print("Partial assignments: ", partial_assignments)
  
    # For each partial assignment, we create all possible mappings that complete the assignment 
    # (using the remaining pattern nodes that are not connected by edges, and input nodes that 
    # match the attributes and are not already assigned). 
    # Then, we create copies of the partial assignment for each possible completing assignment,
    # and add them to the list of assignments.

    assignments = list()
    for partial_assignment in partial_assignments:
        # Find remaining pattern nodes and input nodes
        remaining_pattern_nodes = set(pattern.nodes) - set(partial_assignment.keys())
        if not remaining_pattern_nodes:
            assignments.append(partial_assignment)
            continue

        remaining_input_nodes = set(graph.nodes) - set(partial_assignment.values())
        completing_assignments = list()

        # Get all permutations of the remaining input nodes that could be mapped to the remaining pattern nodes
        possible_mappings = permutations(remaining_input_nodes, len(remaining_pattern_nodes))

        # Create completing assignments by mapping remaining pattern nodes to input nodes for each permutation
        for perm in possible_mappings:
            completing_assignment = dict()
            for pattern_node, input_node in zip(remaining_pattern_nodes, perm):
                completing_assignment[pattern_node] = input_node
            completing_assignments.append(completing_assignment)

        # Add the completing assignments to the overall list of assignments
        for completing_assignment in completing_assignments:
            new_assignment = {pattern_node: input_node for pattern_node, input_node in partial_assignment.items()}
            new_assignment.update(completing_assignment)
            assignments.append(new_assignment)
                
    #STAVS DEBUG
    print("Assignments: ", assignments)

    # Filter and yield valid subgraphs that match the pattern (structurally and by attributes)
    for assignment in assignments:
        subgraph = graph.subgraph(assignment.values())
        yield subgraph, assignment

    #TODO: show Dean what happens when we use the isomorphism function - it removes mappings where if there isn't an edge 
    # between two nodes in the pattern, it doesn't allow them to be mapped in the assignment
    # # Validate the subgraph for isomorphism against the pattern
    #     if isomorphism.is_isomorphic(subgraph, pattern, node_match=_attributes_match, edge_match=_attributes_match):
    #         yield subgraph, assignment

# %% ../nbs/03_matcher.ipynb 18
FilterFunc = Callable[[Match], bool]

# %% ../nbs/03_matcher.ipynb 21
def _filter_duplicated_matches(matches: list[Match]) -> Iterator[Match]:
    """Remove duplicates from a list of Matches, based on their mappings. Return an iterator of the matches without duplications.

    Args:
        matches (list[Match]): list of Match objects

    Yields:
        Iterator[list[Match]]: Iterator of the matches without duplications.
    """

    # We can't use a set directly because Match objects are not hashable. 
    # This is why we use a list of matche's mappings to check for duplicates.
    mappings = []
    for match in matches:
        if match.mapping not in mappings:
            mappings.append(match.mapping)
            yield match

# %% ../nbs/03_matcher.ipynb 22
def _find_intersecting_pattern_nodes(exact_match_pattern: DiGraph, collection_pattern: DiGraph) -> set:
    """
    Find the intersecting pattern nodes between the exact match pattern and the collection pattern.

    The intersecting pattern nodes are those that appear in both the exact match pattern 
    (i.e., pattern nodes that aim to match a single, unique input node) and the collection pattern 
    (i.e., pattern nodes that aim to match multiple input nodes).

    Args:
        exact_match_pattern (DiGraph): The pattern graph representing nodes that match exactly one input node.
        collection_pattern (DiGraph): The pattern graph representing nodes that match multiple input nodes.

    Returns:
        set: A set of pattern nodes that are present in both the exact match pattern and the collection pattern.
    """
    intersecting_pattern_nodes = set(exact_match_pattern.nodes) & set(collection_pattern.nodes)
    return intersecting_pattern_nodes


#| export
def _add_collections_to_exact_matches(input_graph: DiGraph, collection_pattern: DiGraph, 
                                      exact_matches: Set[Dict[NodeName, NodeName]], intersecting_pattern_nodes: Set[NodeName]
                                      ) -> Iterator[Dict[NodeName, Set[NodeName]]]:
    """
    Add collection matches to the existing exact matches by finding subgraph matches for collection pattern nodes
    and merging them with the given exact match mapping.

    This function finds matches in the input graph that satisfy both the exact match pattern (pattern nodes 
    that aim to match exactly one input node) and the collection pattern (pattern nodes that aim to match 
    multiple input nodes).

    Args:
        input_graph (DiGraph): The input graph where collection matches are searched.
        collection_pattern (DiGraph): The pattern graph representing nodes that match multiple input nodes.
        exact_matches (Set[Dict[NodeName, NodeName]]): The set of exact matches, where each pattern node 
            is mapped to a single input node.
        intersecting_pattern_nodes (Set[NodeName]): The set of pattern nodes that intersect between the 
            exact match pattern and collection pattern.

    Yields:
        Iterator[Dict[NodeName, Set[NodeName]]]: An iterator over the updated mappings, where each includes both 
        the previous exact match mapping and the newly found collection matches for this exact match.
    """
    input_graph_copy = input_graph.copy()

    # Enrich the exact match mapping with the corresponding collection matches.
    # This involves moving to set semantics for exact matches nodes and adding collection matches.
    for exact_match in exact_matches:
        updated_mapping = {pattern_node: {input_node} for pattern_node, input_node in exact_match.items()}
        non_intersecting_collection_pattern_nodes = set(collection_pattern.nodes) - intersecting_pattern_nodes
        updated_mapping.update({pattern_node: set() for pattern_node in non_intersecting_collection_pattern_nodes})

        # Lock intersecting pattern nodes to their corresponding input node in the exact match
        collection_pattern_copy = collection_pattern.copy()
        for intersecting_pattern_node in intersecting_pattern_nodes:
            collection_pattern_copy.nodes[intersecting_pattern_node]['_id'] = exact_match[intersecting_pattern_node]

        # Find collection matches using the locked pattern
        collection_matches = list(_find_pattern_based_matches(input_graph_copy, collection_pattern_copy))

        # Add matches for collection pattern nodes
        for collection_match in collection_matches:
            for collection_pattern_node, matched_input_nodes in collection_match.items():
                if collection_pattern_node not in intersecting_pattern_nodes: # We already have the exact match for these nodes
                    updated_mapping[collection_pattern_node].add(matched_input_nodes)  # Add the matched input node

        yield updated_mapping
