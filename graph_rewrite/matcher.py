# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_matcher.ipynb.

# %% auto 0
__all__ = ['FilterFunc', 'find_intersecting_nodes', 'add_collections', 'find_matches']

# %% ../nbs/03_matcher.ipynb 5
from typing import *
from networkx import DiGraph
from networkx.algorithms import isomorphism # check subgraph's isom.
import itertools # iterating over all nodes\edges combinations

from .core import NodeName, _create_graph, draw
from .lhs import lhs_to_graph
from .match_class import Match, mapping_to_match, is_anonymous_node,draw_match

# %% ../nbs/03_matcher.ipynb 8
def _attributes_exist(input_graph_attrs: dict, pattern_attrs: dict) -> bool:
    """Given an input-graph node and a pattern node, checks whether the input-graph node
    has all the attributes which the pattern node requires. If it does, then this input-graph node might be matched as that pattern node.
    
    Note that we only refer to the existence of attributes here, i.e. if both nodes have the same attributes but with
    different values, this function still considers them as a potential pair to match.

    Args:
        input_graph_attrs (dict): Attributes of some input-graph node.
        pattern_attrs (dict): Attributes of some pattern-graph node.

    Returns:
        bool: True if the input-graph node has all the attributes which the pattern node requires, False otherwise.
    """
    return set(pattern_attrs.keys()).issubset(set(input_graph_attrs.keys()))

# %% ../nbs/03_matcher.ipynb 10
def _does_node_match_pattern(graph_node_attrs: dict, pattern: DiGraph) -> bool:
    """Given the attributes of some input-graph node, checks whether this node
    has the same attributes as some node in the pattern graph. If it does,
    then the node by match that node in the pattern - and thus, might be included
    in a subgraph that will match the entire pattern.

    Args:
        graph_node_attrs (dict): Attributes of some input-graph node.
        pattern (DiGraph): A pattern graph produced by the LHS Parser.

    Returns:
        bool: True if the input-graph node has the same attributes as some pattern node, False otherwise.
    """
    return any([_attributes_exist(graph_node_attrs, pattern_attr) for (_, pattern_attr) in pattern.nodes(data=True)])

# %% ../nbs/03_matcher.ipynb 12
# Collections Feature - in order to get structural matches where certain nodes (intersecting ones) are guranteed to have a specific
# mapping in the original graph, we add a node_mapping argument, a dict[NodeName, NodeName] that would help with this pruning
# node_mapping would be empty by default
def _find_structural_matches(graph: DiGraph, pattern: DiGraph) -> Tuple[DiGraph, dict[NodeName, NodeName]]:
    """Given a graph, find all of its subgraphs which have the same structure (same nodes and edges)
    as a given pattern DiGraph. That is, all subgraphs which are isomorphic to the pattern.

    Args:
        graph (DiGraph): A graph to find matches in
        pattern (DiGraph): A pattern graph produced by the LHS Parser.

    Yields:
        Iterator[Tuple[DiGraph, dict[NodeName, NodeName]]]: Iterator of (subgraph, mapping) tuples,
            where for each pair, the subgraph is the subset of nodes and edges in the input graph that
            match the pattern, and the mapping is a dictionary that maps nodes in that subgraph
            to nodes in the pattern.
    """
    # a function that would create only the combinations that contains the intersecting nodes. if the intersecting nodes are empty
    # it would work the same as itertools.combinations # Collections Feature
    def combinations_with_intersects(iterable, r, intersects):
        without_forced = [item for item in iterable if item not in intersects]
        combs = itertools.combinations(without_forced, r - len(intersects))
        yield from [comb + intersects for comb in combs]
    
    # TODO: replace itertools.combinations with combinations_with_intersects # Collections Feature
    for sub_nodes in itertools.combinations(graph.nodes, len(pattern.nodes)):
        nodes_subg: DiGraph = graph.subgraph(sub_nodes)
        for sub_edges in itertools.combinations(nodes_subg.edges(data=True), len(pattern.edges)):
            # Create a subgraph with selected edges and nodes
            subg = DiGraph()
            subg.add_nodes_from(list(nodes_subg.nodes(data=True)))
            subg.add_edges_from(list(sub_edges))

            # Find structural matches with the selected edges and nodes
            matcher = isomorphism.DiGraphMatcher(pattern, subg)
            for isom_mapping in matcher.isomorphisms_iter():
                # TODO: add a check that isom_mapping does not contradict node_mapping
                yield (nodes_subg, isom_mapping)



''' # Collections Feature - replace find_structural_matches with more efficient way of pruning
def find_structural_matches(pattern,g):

  possible_candidates={
  node_name:nodes_that_match_on_attributes(pattern[node_name],g)
  }

  for node_options in itertools.product(node,possible_candidates.values()):
  subgraph = g.subgraph(node_options)
  if isomorphism (pattern,sub_graph)
    yield subgraph

example pattern:
- { 'x':{a=b}, 'y':{}} # first phase
- { 'x':{a=b,_id=1}, 'y':{}} # second phase
'''

# %% ../nbs/03_matcher.ipynb 14
def _does_isom_match_pattern(isom: Tuple[DiGraph, dict], pattern: DiGraph) -> bool:
    """Given a graph that is isomorphic to the pattern, checks whether they also
    match in terms of their attributes (that is, the graph has the same attributes
    as the pattern). If they does, then the isomorphic graph matches the pattern completely.

    Args:
        isom (Tuple[DiGraph, dict]): A graph that's isomorphic to the pattern
        pattern (DiGraph): A pattern graph produced by the LHS Parser.

    Returns:
        bool: True if the isomorphic graph matches the pattern, False otherwise.
    """

    # check nodes match
    subgraph, mapping = isom
    if not all([_attributes_exist(subgraph.nodes[original_node], pattern.nodes[pattern_node]) \
                for (pattern_node, original_node) in mapping.items()]):
        return False

    # check edges match
    if all([_attributes_exist(subgraph.edges[mapping[edge[0]], mapping[edge[1]]], edge[2]) \
                for edge in pattern.edges(data=True)]):
        return True

# %% ../nbs/03_matcher.ipynb 16
FilterFunc = Callable[[Match], bool]

# %% ../nbs/03_matcher.ipynb 19
def _remove_duplicated_matches(matches: list[Match]) -> Match:
    """Remove duplicates from a list of Matches, based on their mappings. Return an iterator of the matches without duplications.

    Args:
        matches (list[Match]): list of Match objects

    Yields:
        Iterator[list[Match]]: Iterator of the matches without duplications.
    """
    new_list = []
    for match in matches:
        if match not in new_list:
            new_list.append(match)
            yield match

# %% ../nbs/03_matcher.ipynb 20
# Collections Feature
def find_intersecting_nodes(match: Match, collection_pattern: DiGraph):
    # Step 1: Extract all node names from self._nodes and the node collections (if they do not exist yet, they will be empty - no harm is done).
    # Step 2: Find all nodes with the same name in collection_pattern - these are the intersecting nodes.
    # Step 3: Return all matching node names.

    pass

# Collections Feature
def add_collections(match: Match, collection_pattern: DiGraph):
    # Step 1: Call find_intersecting_nodes
    # Step 2: Make the first two steps in find_matches
    # Step 3: Call an adjusted _find_structural_matches with a mapping of intersecting nodes and their corresponding nodes in the graph
    # Step 4: Make the fourth step in find_matches - call _does_isom_match_pattern
    # Step 5: Use the resulted mappings and the collection_pattern to create corresponding collections from the nodes and edges and 
    #         add them to the match.collections
    pass



# %% ../nbs/03_matcher.ipynb 22
#TODO: add collections_pattern argument # Collections Feature
def find_matches(input_graph: DiGraph, pattern: DiGraph, condition: FilterFunc = lambda match: True) -> Match:
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

    # Narrow down search space by keeping only input-graph nodes that have the same attributes as some pattern node
    matching_nodes = [n for (n, attrs) in input_graph.nodes(data=True) if _does_node_match_pattern(attrs, pattern)]
    # Reducing the input graph to the matching nodes + connected edges
    reduced_input_g = input_graph.subgraph(matching_nodes)
    
    # Find all structural matches (isomorphisms), ignore attributes
    isom_matches =  [match for match in _find_structural_matches(reduced_input_g, pattern)]
    # Find matches with attributes among isoms (match pattern's attributes)
    attribute_matches = [mapping for (subgraph, mapping) in isom_matches if _does_isom_match_pattern((subgraph, mapping), pattern)]

    # construct a list of Match objects. Note that the condition is checked on a Match that includes anonymous nodes (as it might use it)
    # but the Match that we return does not include the anonymous parts.
    # Therefore, we first construct a list of tuples - the first is the mapping with anonymous, the second isn't
    matches_list = [(mapping_to_match(input_graph, pattern, mapping, filter=False), mapping_to_match(input_graph, pattern, mapping)) 
                    for mapping in attribute_matches]
    # Then filter the list, to contain only the filtered match whose unfiltered version matches the condition
    filtered_matches =  [filtered_match for (unfiltered_match, filtered_match) in matches_list if condition(unfiltered_match)]
    # And finally, remove duplicates (might be created because we removed the anonymous nodes)
    #TODO: call add_collections for each match in _remove_duplicated_matches(filtered_matches) and yield from the result # Collections Feature
    """
    filtered_matches = _remove_duplicated_matches(filtered_matches)
    for match in filtered_matches:
          add_collections(match, collections_pattern)
    yield from filtered_matches
    """
    yield from _remove_duplicated_matches(filtered_matches)


    ''' # Collections Feature - change find_matches to work according to the new find_structural_matches 
    def find_matches(pattern,collection_pattern,g,condition_funcs):
  
        for phase_1_iso in  find_structural_matches(pattern,g):
            phase_1_match = pattern.copy()
            # add _id constrains from phase_1_iso
            # find intersection nodes ....
        phase_2_isos = [phase_2_iso in find_structural_matches(collection_pattern_with_id_constraints,g)]  
        match = Match(regular_nodes = pahse_1_iso,collections = phase_2_isos)  
        if condition(match):
            yield match
    '''
