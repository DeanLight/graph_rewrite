# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/06_transform.ipynb.

# %% auto 0
__all__ = ['rewrite_iter', 'rewrite']

# %% ../nbs/06_transform.ipynb 5
from typing import *
from networkx import DiGraph
from copy import deepcopy
from fastcore.meta import delegates

from .core import NodeName, EdgeName, _create_graph, draw, _graphs_equal, GraphRewriteException
from .lhs import lhs_to_graph
from .match_class import Match, mapping_to_match,draw_match
from .matcher import find_matches, FilterFunc
from .p_rhs_parse import RenderFunc, p_to_graph, rhs_to_graph
from .rules import Rule, MergePolicy

# %% ../nbs/06_transform.ipynb 7
_exception_msgs = {
    "no_such_node": lambda node: f"Node {node} does not exist in the input graph.",
    "no_such_edge": lambda edge: f"Edge {edge} does not exist in the input graph.",
    "no_such_attr_in_node": lambda attr, node: f"Attribute {attr} does not exist in input graph's node {node}.",
    "no_such_attr_in_edge": lambda attr, edge: f"Attribute {attr} does not exist in input graph's edge {edge}.",
    "edge_exists": lambda edge: f"Edge {edge} already exists in the input graph.",
    "not_enough_to_merge": lambda: f"Tried to merge less than one nodes."
}

# %% ../nbs/06_transform.ipynb 8
def _generate_new_node_name(graph: DiGraph, base_name: NodeName) -> NodeName:
    """Generate a name for a new node, which is unique in the graph to which the node is added,
    based on an initial name suggestion.
    If that suggested name does not exist in the graph, it is used for the new node.
    Otherwise, the new node's name will have the suggested name as a prefix, followed by a serial number (<name>_<num>)
    that makes sure that the name is unique but not too long.

    Args:
        graph (DiGraph): A graph to which the new node is added
        base_name (NodeName): The initial suggestion for the new node's desired name

    Returns:
        NodeName: The name chosen for the new node
    """
    new_name = base_name
    i = 0
    while new_name in graph.nodes():
        i += 1
        new_name = f"{base_name}_{i}"
    return new_name

# %% ../nbs/06_transform.ipynb 9
def _clone_node(graph: DiGraph, node_to_clone: NodeName) -> NodeName:
    """Clones a node in the graph. That is, create a new node, whose name denotes its connection to the original node,
    whose edges are copies of the edges connected to the original node, and whose attributes are duplicated
    from the original node.

    Args:
        graph (DiGraph): A graph
        node_to_clone (NodeName): A node in the graph to be cloned

    Raises:
        GraphRewriteException: If the node which should be cloned does not exist in the graph

    Returns:
        NodeName: The name of the new cloned node
    """
    if node_to_clone not in graph.nodes:
        raise GraphRewriteException(_exception_msgs["no_such_node"](node_to_clone))

    # Create a new node name
    clone_name = _generate_new_node_name(graph, node_to_clone)

    # Add this new node to graph
    cloned_node_attrs = graph.nodes(data=True)[node_to_clone]
    graph.add_node(clone_name, **cloned_node_attrs)

    # Clone edges (connect the clone to all original edge endpoints + copy attrs)
    for n, _ in graph.in_edges(node_to_clone):
        if (n, clone_name) not in graph.edges():
            cloned_edge_attrs = graph.edges[n, node_to_clone]
            graph.add_edge(n, clone_name, **cloned_edge_attrs)
    
    for _, n in graph.out_edges(node_to_clone):
        if (clone_name, n) not in graph.edges():
            cloned_edge_attrs = graph.edges[node_to_clone, n]
            graph.add_edge(clone_name, n, **cloned_edge_attrs)
 
    return clone_name

# %% ../nbs/06_transform.ipynb 10
def _remove_node(graph: DiGraph, node_to_remove: NodeName):
    """Remove a node from the graph.

    Args:
        graph (DiGraph): A graph
        node_to_remove (NodeName): A node to remove from the graph

    Raises:
        GraphRewriteException: If the removed node doesn't exist in the graph
    """
    if node_to_remove not in graph.nodes():
        raise GraphRewriteException(_exception_msgs["no_such_node"](node_to_remove))
    graph.remove_node(node_to_remove)

# %% ../nbs/06_transform.ipynb 11
def _remove_edge(graph: DiGraph, edge_to_remove: EdgeName):
    """Remove an edge from the graph.

    Args:
        graph (DiGraph): A graph
        edge_to_remove (EdgeName): An edge to remove from the graph

    Raises:
        GraphRewriteException: If the removed edge doesn't exist in the graph
    """
    if edge_to_remove not in graph.edges():
        raise GraphRewriteException(_exception_msgs["no_such_edge"](edge_to_remove))
    graph.remove_edge(*edge_to_remove)

# %% ../nbs/06_transform.ipynb 12
def _remove_node_attrs(graph: DiGraph, node: NodeName, attrs_to_remove: set):
    """Remove a subset of some node's attributes from the node.

    Args:
        graph (DiGraph): A graph
        node (NodeName): A node in the graph
        attrs_to_remove (set): Attributes of that node to remove

    Raises:
        GraphRewriteException: If the node doesn't exist in the graph, or some of the removed attrs don't exist in the node
    """
    if node not in graph.nodes():
        raise GraphRewriteException(_exception_msgs["no_such_node"](node))
    for attr in attrs_to_remove:
        if attr not in graph.nodes[node]:
            raise GraphRewriteException(_exception_msgs["no_such_attr_in_node"](attr, node))
        del graph.nodes[node][attr]

# %% ../nbs/06_transform.ipynb 13
def _remove_edge_attrs(graph: DiGraph, edge: EdgeName, attrs_to_remove: set):
    """Remove a subset of some edge's attributes from the node.

    Args:
        graph (DiGraph): A graph
        edge (EdgeName): An edge in the graph
        attrs_to_remove (set): Attributes of that edge to remove

    Raises:
        GraphRewriteException: If the edge doesn't exist in the graph, or some of the removed attrs don't exist in the edge
    """

    if edge not in graph.edges():
        raise GraphRewriteException(_exception_msgs["no_such_edge"](edge))
    for attr in attrs_to_remove:
        if attr not in graph.edges[edge]:
            raise GraphRewriteException(_exception_msgs["no_such_attr_in_edge"](attr, edge))
        del graph.edges[edge][attr]

# %% ../nbs/06_transform.ipynb 14
def _setup_merged_node(graph: DiGraph, nodes_to_merge: set[NodeName], merge_policy: MergePolicy):
    """A helper function for node merging. It calculates all the parameters needed for creating the merged node,
    such as its name, its attributes, the connected edges and their attributes, etc., and returns them all.
    In addition, it removes the original nodes (which are about to be merged) from the graph.

    Args:
        graph (DiGraph): A graph
        nodes_to_merge (set[NodeName]): A set of nodes in the graph to merge
        merge_policy (MergePolicy): A policy that dictates how to merge conflicting attributes

    Returns:
        All the parameters needed for creating the merged node, in this order:
        - The name of the merged node
        - The attrs of the merged node
        - The nodes that are sources of new edges to the merged node
        - The nodes that are targets of new edges from the merged node
        - The attrs of the new edges to the merged node
        - The attrs of the new edges from the merged node
        - A boolean value for whether the new merged node has a self loop (a special case)
        - The attributes of the selp loop, in case such edge exists
    """
    merged_node_name = _generate_new_node_name(graph, "&".join(nodes_to_merge))
    
    merged_node_attrs = {}
    merged_src_nodes, merged_target_nodes = set(), set()
    merged_src_attrs, merged_target_attrs = {}, {} # map a src/target node to the edge's merged attrs
    self_loop, self_loop_attrs = False, {}
    
    for node_to_merge in nodes_to_merge:
        merged_node_attrs = merge_policy(merged_node_attrs, graph.nodes[node_to_merge])
        
        in_edges, out_edges = graph.in_edges(node_to_merge), graph.out_edges(node_to_merge)
        merged_src_nodes.update({s if s not in nodes_to_merge else merged_node_name for s, _ in in_edges})
        merged_target_nodes.update({t if t not in nodes_to_merge else merged_node_name for _, t in out_edges})

        for edge in in_edges:
            edge_attrs, src = graph.edges[edge], edge[0]
            # Add to source attributes
            if src not in merged_src_attrs.keys():
                merged_src_attrs[src] = edge_attrs
            else:
                merged_src_attrs[src] = merge_policy(merged_src_attrs[src], edge_attrs)

            # Handle selp loop
            if src in nodes_to_merge:
                self_loop = True
                self_loop_attrs = merge_policy(self_loop_attrs, edge_attrs)
            
        for edge in out_edges:
            edge_attrs, target = graph.edges[edge], edge[1]
            # Add to source attributes
            if target not in merged_target_attrs.keys():
                merged_target_attrs[target] = edge_attrs
            else:
                merged_target_attrs[target] = merge_policy(merged_target_attrs[target], edge_attrs)

            # Handle selp loop
            if target in nodes_to_merge:
                self_loop = True
                self_loop_attrs = merge_policy(self_loop_attrs, edge_attrs)

        graph.remove_node(node_to_merge)

    return merged_node_name, merged_node_attrs, merged_src_nodes, merged_target_nodes,\
            merged_src_attrs, merged_target_attrs, self_loop, self_loop_attrs

# %% ../nbs/06_transform.ipynb 15
def _merge_nodes(graph: DiGraph, nodes_to_merge: set[NodeName], merge_policy: MergePolicy) -> NodeName:
    """Merge a set of nodes in the graph. That is, remove all these nodes and replace them with a new node,
    whose attributes merge the attributes of the original nodes, whose connected edges merge the edges connected to
    the original node, and whose name denotes the nodes which it merges.

    Args:
        graph (DiGraph): A graph
        nodes_to_merge (set[NodeName]): A set of nodes to merge
        merge_policy (MergePolicy): A policy that dictates how to merge conflicting attributes

    Raises:
        GraphRewriteException: If the set of nodes to merge is too small (less than two nodes), or if one of them doesn't
        exist in the graph.

    Returns:
        NodeName: The name of the new merged node
    """
    if len(nodes_to_merge) < 1:
        raise GraphRewriteException(_exception_msgs["not_enough_to_merge"]())
    elif len(nodes_to_merge) == 1:
        return list(nodes_to_merge)[0]
    for node_to_merge in nodes_to_merge:
        if node_to_merge not in graph.nodes:
            raise GraphRewriteException(_exception_msgs["no_such_node"](node_to_merge))

    merged_node_name, merged_node_attrs, merged_src_nodes, merged_target_nodes, \
        merged_src_attrs, merged_target_attrs, self_loop, self_loop_attrs = _setup_merged_node(graph, node_to_merge, merge_policy)

    # Add merged node to graph
    graph.add_node(merged_node_name, **merged_node_attrs)

    # Add merged source and target edges (including a new self loop)
    if self_loop:
        graph.add_edge(merged_node_name, merged_node_name, **self_loop_attrs)
    for src_node in merged_src_nodes:
        if (src_node, merged_node_name) not in graph.edges():
            graph.add_edge(src_node, merged_node_name)
    for target_node in merged_target_nodes:
        if (merged_node_name, target_node) not in graph.edges():
            graph.add_edge(merged_node_name, target_node)
    
    # Add edge attributes (other than selp loop)
    for src_node, attrs in merged_src_attrs.items():
        if src_node not in nodes_to_merge:
            graph.update(edges=[(src_node, merged_node_name, attrs)])
    for target_node, attrs in merged_target_attrs.items():
        if target_node not in nodes_to_merge:
            graph.update(edges=[(merged_node_name, target_node, attrs)])

    return merged_node_name

# %% ../nbs/06_transform.ipynb 16
def _add_node(graph: DiGraph, node_to_add: NodeName) -> NodeName:
    """Add a new node to the graph.

    Args:
        graph (DiGraph): A graph
        node_to_add (NodeName): The desired name of the new node

    Returns:
        NodeName: The name of the new added node (based on the name suggested)
    """
    # Create a new node name
    new_name = _generate_new_node_name(graph, node_to_add)
    graph.add_node(new_name)
    return new_name

# %% ../nbs/06_transform.ipynb 17
def _add_edge(graph: DiGraph, edge_to_add: EdgeName):
    """Add an edge to the graph.

    Args:
        graph (DiGraph): A graph
        edge_to_add (EdgeName): The edge to add.

    Raises:
        GraphRewriteException: If one of the edge's endpoints doesn't exist in the graph, or the edge itself already exists.
    """
    src, target = edge_to_add
    if src not in graph.nodes():
        raise GraphRewriteException(_exception_msgs["no_such_node"](src))
    elif target not in graph.nodes():
        raise GraphRewriteException(_exception_msgs["no_such_node"](target))
    elif edge_to_add in graph.edges():
        raise GraphRewriteException(_exception_msgs["edge_exists"](edge_to_add))
    else:
        graph.add_edge(src, target)

# %% ../nbs/06_transform.ipynb 18
def _add_node_attrs(graph: DiGraph, node: NodeName, attrs_to_add: dict):
    """Add attributes to a node in the graph.

    Args:
        graph (DiGraph): A graph
        node (NodeName): A node in the graph
        attrs_to_add (dict): Attributes to add to the node

    Raises:
        GraphRewriteException: If the node doesn't exist in the graph
    """
    if node not in graph.nodes():
        raise GraphRewriteException(_exception_msgs["no_such_node"](node))
    for attr, val in attrs_to_add.items():
        graph.nodes[node][attr] = val

# %% ../nbs/06_transform.ipynb 19
def _add_edge_attrs(graph: DiGraph, edge: EdgeName, attrs_to_add: dict):
    """Add attributes to an edge in the graph.

    Args:
        graph (DiGraph): A graph
        edge (EdgeName): An edge in the graph
        attrs_to_add (dict): Attributes to add to the edge

    Raises:
        GraphRewriteException: If the edge doesn't exist in the graph
    """
    if edge not in graph.edges():
        raise GraphRewriteException(_exception_msgs["no_such_edge"](edge))
    for attr, val in attrs_to_add.items():
        graph.edges[edge][attr] = val

# %% ../nbs/06_transform.ipynb 21
_GREEN = '\033[92m'
_RED = '\033[91m'
_BLACK = '\033[0m'

def _log(msg: str, is_log: bool, color: str = _BLACK):
    """Logging some message to the console.

    Args:
        msg (str): A message to log
        is_log (bool): If True, the log is printed (otherwise, it isn't).
        color (str, optional): A color for the printed message. Defaults to _BLACK.
    """
    if is_log:
        print(f"{color}{msg}{_BLACK}")

# %% ../nbs/06_transform.ipynb 22
def _rewrite_match_restrictive(input_graph: DiGraph, rule: Rule, lhs_input_map: dict[NodeName, NodeName], is_log: bool) -> dict[NodeName, NodeName]:
    """Performs the restrictive phase of the rewriting process on some match: Clone nodes, Remove nodes and edges (and/or their attributes).

    Args:
        input_graph (DiGraph): A graph to rewrite
        rule (Rule): A rule that dictates what transformations should the graph go through
        lhs_input_map (dict[NodeName, NodeName]): Maps names of LHS nodes to names of input graph nodes, based on the match which we rewrite
        is_log (bool): If True, logs are printed throughout the process.

    Returns:
        dict[NodeName, NodeName]: maps names of P nodes to names of input graph nodes
    """

    # Initialize an empty mapping from P nodes to input_graph nodes.
    p_input_map = {}

    """Clone nodes:
        Find all LHS nodes that should be cloned (and what are their clones in P).
        For each clone of an LHS node (apart from the first one), add it to the input graph 
        (clone with edges and attributes) and add the pair (clone_name, lhs_node_name) to the p->input mapping.
    """
    # Map each cloned lhs node to a flag, denoting whether the original node is reused with the same name in P.
    # If not, the original node will be removed later
    cloned_to_flags_map = {cloned_lhs_node: False for cloned_lhs_node in rule.nodes_to_clone().keys()}
    for cloned_lhs_node, p_clones in rule.nodes_to_clone().items():
        for p_clone in p_clones:
            # Original cloned node is reused in P, preserve it
            if p_clone == cloned_lhs_node:
                _log(f"Clone {lhs_input_map[cloned_lhs_node]}", is_log)
                cloned_to_flags_map[cloned_lhs_node] = True
                p_input_map[p_clone] = lhs_input_map[cloned_lhs_node]
            # All other clones require actual cloning (mapped to the new cloned node in input graph)
            else:
                new_clone_id = _clone_node(input_graph, lhs_input_map[cloned_lhs_node])
                _log(f"Clone {lhs_input_map[cloned_lhs_node]} as {new_clone_id}", is_log)
                p_input_map[p_clone] = new_clone_id

    """Remove nodes, complete p->input mapping with preserved nodes which are not clones:
        Find all LHS nodes that should be removed. 
        For each LHS node, if should be removed - remove it from input.
                            otherwise, if it is not a clone, add to the mapping.
    """
    for lhs_node in rule.lhs.nodes():
        # Cloned lhs nodes which weren't reused and so, should be deleted
        if lhs_node in rule.nodes_to_remove() or (lhs_node in cloned_to_flags_map.keys() and cloned_to_flags_map[lhs_node] == False):
            _log(f"Remove node {lhs_input_map[lhs_node]}", is_log)
            _remove_node(input_graph, lhs_input_map[lhs_node])        
        # Else, either a saved cloned node (already preserved) or a regular one (should preserve them)
        elif lhs_node not in cloned_to_flags_map.keys():
            p_node = list(rule._rev_p_lhs[lhs_node])[0]
            p_input_map[p_node] = lhs_input_map[lhs_node]

    # Remove edges.
    for lhs_src, lhs_target in rule.edges_to_remove():
        _log(f"Remove edge ({p_input_map[lhs_src]}, {p_input_map[lhs_target]})", is_log)
        _remove_edge(input_graph, (p_input_map[lhs_src], p_input_map[lhs_target]))

    # Remove node attrs.
    for p_node, attrs_to_remove in rule.node_attrs_to_remove().items():
        _log(f"Remove attrs {attrs_to_remove} from node {p_input_map[p_node]}", is_log)
        _remove_node_attrs(input_graph, p_input_map[p_node], attrs_to_remove)

    # Remove edge attrs.
    for (p_src, p_target), attrs_to_remove in rule.edge_attrs_to_remove().items():
        _log(f"Remove attrs {attrs_to_remove} from edge {(p_input_map[p_src], p_input_map[p_target])}", is_log)
        _remove_edge_attrs(input_graph, (p_input_map[p_src], p_input_map[p_target]), attrs_to_remove)

    return p_input_map

# %% ../nbs/06_transform.ipynb 23
def _rewrite_match_expansive(input_graph: DiGraph, rule: Rule, p_input_map: dict[NodeName, NodeName], is_log: bool):
    """Performs the expansive phase of the rewriting process on some match: Merge nodes, Remove Add and edges (and/or new or updated attributes).

    Args:
        input_graph (DiGraph): A graph to rewrite
        rule (Rule): A rule that dictates what transformations should the graph go through
        p_input_map (dict[NodeName, NodeName]): Maps names of P nodes to names of input graph nodes, based on the match which we rewrite
        is_log (bool): If True, logs are printed throughout the process.
    """
        
    # Initialize an empty mapping from RHS nodes to input_graph nodes.
    rhs_input_map = {}

    """Merge nodes:
        Find all RHS nodes that are a merge of P nodes (and what P nodes they merge).
        For each RHS node that is a merge, merge all of the relavant P node, add the resulting RHS node to the input.
        Also removes from input the P nodes that were merged into a new node.
        Save the new RHS merged node to the RHS->input mapping.
    """
    merge_rhs_nodes = rule.nodes_to_merge().keys()
    for merge_rhs_node, p_merged in rule.nodes_to_merge().items():
        input_nodes_to_merge = {p_input_map[p_node] for p_node in p_merged}
        new_merged_id = _merge_nodes(input_graph, input_nodes_to_merge, rule.merge_policy)
        _log(f"Merge {input_nodes_to_merge} as {new_merged_id}", is_log)
        rhs_input_map[merge_rhs_node] = new_merged_id
        
    """Add nodes, complete RHS->input mapping with added (and preserved) nodes:
        Find all RHS nodes that should be added to the input (not including nodes that are a merge of P noeds).
        For each RHS node, if should be added - add it to input and to the RHS->input mapping.
                            otherwise, if is not a merge - add to the mapping.
    """
    for rhs_node in rule.rhs.nodes():
        if rhs_node in rule.nodes_to_add():
            added_id = _add_node(input_graph, rhs_node)
            _log(f"Add node {rhs_node} as {added_id}", is_log)
            rhs_input_map[rhs_node] = added_id
        elif rhs_node not in merge_rhs_nodes:
            p_node = list(rule._rev_p_rhs[rhs_node])[0]
            rhs_input_map[rhs_node] = p_input_map[p_node]

    # Add edges.
    for rhs_src, rhs_target in rule.edges_to_add():
        _log(f"Add edge ({rhs_input_map[rhs_src]}, {rhs_input_map[rhs_target]})", is_log)
        _add_edge(input_graph, (rhs_input_map[rhs_src], rhs_input_map[rhs_target]))

    # Add node attrs.
    for rhs_node, attrs_to_add in rule.node_attrs_to_add().items():
        _log(f"Added attrs {attrs_to_add} to node {rhs_input_map[rhs_node]}", is_log)
        _add_node_attrs(input_graph, rhs_input_map[rhs_node], attrs_to_add)

    # Add edge attrs.
    for (rhs_src, rhs_target), attrs_to_add in rule.edge_attrs_to_add().items():
        _log(f"Added attrs {attrs_to_add} to edge {(rhs_input_map[rhs_src], rhs_input_map[rhs_target])}", is_log)
        _add_edge_attrs(input_graph, (rhs_input_map[rhs_src], rhs_input_map[rhs_target]), attrs_to_add)

# %% ../nbs/06_transform.ipynb 25
def _copy_graph(graph: DiGraph) -> DiGraph:
    """Creates a copy of the graph (including attributes, which are deep-copied).

    Args:
        graph (DiGraph): A graph to copy

    Returns:
        DiGraph: The new copy of the graph
    """
    copied_nodes = [(node, deepcopy(attrs)) for node, attrs in graph.nodes(data=True)]
    copied_edges = [(s, t, deepcopy(attrs)) for s, t, attrs in graph.edges(data=True)]
    copy_graph = DiGraph()
    copy_graph.update(nodes=copied_nodes, edges=copied_edges)
    return copy_graph

# %% ../nbs/06_transform.ipynb 26
def _restore_graph(graph: DiGraph, last_copy_graph: DiGraph):
    """Change a graph according to some "checkpoint".

    Args:
        graph (DiGraph): A graph to change
        last_copy_graph (DiGraph): The "checkpoint" to which the graph is restored
    """
    graph.clear()
    graph.update(nodes=last_copy_graph.nodes(data=True),
                 edges=last_copy_graph.edges(data=True))

# %% ../nbs/06_transform.ipynb 28
def _rewrite_match(input_graph: DiGraph, match: Match,
                   lhs_graph: DiGraph, p_graph: DiGraph, rhs: str,
                   render_rhs: dict[str, RenderFunc],
                   merge_policy: MergePolicy,
                   is_log: bool) -> Match:
    """Perform a graph rewriting based on a single match.

    Args:
        input_graph (DiGraph): A graph to rewrite
        match (Match): A single match in the graph
        lhs_graph (DiGraph): A parsed LHS pattern
        p_graph (DiGraph): A parsed P pattern
        rhs (str): A RHS pattern string, with potential placeholders
        render_rhs (dict[str, RenderFunc]): Maps a RHS placeholder to a function that describes how to fill it, based on the given match
        merge_policy (MergePolicy): A policy that dictates how to merge conflicting attributes
        is_log (bool): If True, logs are printed throughout the process.

    Raises:
        GraphRewriteException: if something went wrong during the rewriting process

    Returns:
        Match: The match the we've just rewritten
    """

    _log(f"Transform match: {match.mapping}", is_log, _GREEN)
    # Save graph in current state for restoring, if needed
    saved_graph = _copy_graph(input_graph)

    try:
        # Parse RHS according to current match (with render dictionary)
        rhs_graph = rhs_to_graph(rhs, match, render_rhs) if rhs else None
        # TODO: add collections to rule input # Collections Feature
        rule = Rule(lhs_graph, p_graph, rhs_graph, merge_policy=merge_policy)
        # Transform the graph
        lhs_input_map = match.mapping
        p_input_map = _rewrite_match_restrictive(input_graph, rule, lhs_input_map, is_log)
        _rewrite_match_expansive(input_graph, rule, p_input_map, is_log)
        _log(f"Nodes: {input_graph.nodes(data=True)}\nEdges: {input_graph.edges(data=True)}\n", is_log, _GREEN)
        return match

    except GraphRewriteException as e:
        _log(f"Failed to transform: {e.message}", is_log, _RED)
        _restore_graph(input_graph, saved_graph)
        raise e

# %% ../nbs/06_transform.ipynb 30
def rewrite_iter(input_graph: DiGraph, lhs: str, p: str = None, rhs: str = None,
                   condition: FilterFunc = None,
                   render_rhs: dict[str, RenderFunc] = None,
                   merge_policy: MergePolicy = None,
                   is_log: bool = False,
                   is_recursive: bool = False,
                   display_matches: bool = False,
                   
                   ) -> List[Match]:
    """Perform a graph rewriting using a lazy iterator, yielding the matches one by one after rewriting

    Args:
        input_graph (DiGraph): A graph to rewrite
        lhs (str): A LHS pattern string
        p (str, optional): A P pattern string. Defaults to None.
        rhs (str, optional): A RHS pattern string. Defaults to None.
        condition (FilterFunc, optional): A condition on the matches. Matches for which the condition doesn't hold aren't rewritten. Defaults to lambda match: True.
        render_rhs (dict[str, RenderFunc], optional): Maps a RHS placeholder to a function that describes how to fill it, based on the given match. Defaults to {}.
        merge_policy (MergePolicy, optional): A policy that dictates how to merge conflicting attributes. Defaults to MergePolicy.choose_last.
        is_log (bool, optional): If True, logs are printed throughout the process. Defaults to False.
        is_recursive (bool, optional): If True, matches pool is updated after each rewrite (as that pool might change). Defaults to False.
        display_matches (bool, optional): If True, the matches are displayed, useful for debugging. Defaults to False.

    Yields:
        Iterator[Match]: An iterator of Match instances, which denote the matches we've transformed.
    """
    condition = condition if condition else lambda match: True
    render_rhs = render_rhs if render_rhs else {}
    merge_policy = merge_policy if merge_policy else MergePolicy.choose_last

    _log(f"Nodes: {input_graph.nodes(data=True)}\nEdges: {input_graph.edges(data=True)}\n", is_log, _GREEN)

    # Parse LHS and P (global for all matches)
    lhs_graph, condition = lhs_to_graph(lhs, condition) # Add lhs_collections_graph to the output
    p_graph = p_to_graph(p) if p else None
    
    if is_recursive:
        while True:
            try:
                next_match = next(find_matches(input_graph, lhs_graph, condition=condition))  #TODO: add lhs_collections_graph to find_matches input # Collections Feature
                if display_matches:
                    draw_match(input_graph, next_match)
                yield next_match
                new_res = _rewrite_match(input_graph, next_match, lhs_graph, p_graph, rhs, render_rhs, merge_policy, is_log)
            except StopIteration:
                break

        _log("No more matches.", is_log, _GREEN)

    else:
        # Create a duplication of the graph to find matches lazily (actual graph changes between matches)
        copy_input_graph = _copy_graph(input_graph)

        # Find matches lazily and transform
        for match in find_matches(copy_input_graph, lhs_graph, condition=condition): #TODO: add lhs_collections_graph to find_matches input # Collections Feature
            if display_matches:
                draw_match(input_graph, match)
            # the match object points to the copy graph, so we need to move it to the original graph for imperative changes
            match.set_graph(input_graph)
            yield match
            new_res = _rewrite_match(input_graph, match, lhs_graph, p_graph, rhs, render_rhs, merge_policy, is_log)


# %% ../nbs/06_transform.ipynb 31
@delegates(rewrite_iter)
def rewrite(input_graph: DiGraph, lhs: str,**kwargs
                   ) -> List[Match]:
    """Perform a graph rewriting.

    Args:
        input_graph (DiGraph): A graph to rewrite
        lhs (str): A LHS pattern string
        p (str, optional): A P pattern string. Defaults to None.
        rhs (str, optional): A RHS pattern string. Defaults to None.
        condition (FilterFunc, optional): A condition on the matches. Matches for which the condition doesn't hold aren't rewritten. Defaults to lambda match: True.
        render_rhs (dict[str, RenderFunc], optional): Maps a RHS placeholder to a function that describes how to fill it, based on the given match. Defaults to {}.
        merge_policy (MergePolicy, optional): A policy that dictates how to merge conflicting attributes. Defaults to MergePolicy.choose_last.
        is_log (bool, optional): If True, logs are printed throughout the process. Defaults to False.
        is_recursive (bool, optional): If True, matches pool is updated after each rewrite (as that pool might change). Defaults to False.
        display_matches (bool, optional): If True, the matches are displayed, useful for debugging. Defaults to False.

    Returns:
        Nothing, the graph is transformed in place.
    """
    for _ in rewrite_iter(input_graph, lhs, **kwargs):
        pass

