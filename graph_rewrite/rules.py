# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/05_rules.ipynb.

# %% auto 0
__all__ = ['MergePolicy', 'Rule']

# %% ../nbs/05_rules.ipynb 5
from typing import *
from networkx import DiGraph

from .core import GraphRewriteException, NodeName, EdgeName, _create_graph, draw
from .match_class import *
from .lhs import lhs_to_graph
from .p_rhs_parse import RenderFunc, p_to_graph, rhs_to_graph

# %% ../nbs/05_rules.ipynb 7
class MergePolicy:
    """Static class for policies for solving conflicts when merging nodes with shared attributes.
    """
    @staticmethod
    def _merge_dicts(dict1: dict, dict2: dict, collision_policy: Callable[[Any, Any], Any]) -> dict:
        """A generic dictionary merger, which solves conflicts with a given collision policy.

        Args:
            dict1 (dict): A dictionary
            dict2 (dict): A dictionary
            collision_policy (Callable[[Any, Any], Any]): A function that recieves two values and returns a new value (for solving the conflict).

        Returns:
            dict: The merged dictionary according to the collision policy.
        """
        merged = {}
        for key in dict1.keys():
            if key in dict2.keys():
                merged[key] = collision_policy(dict1[key], dict2[key])
            else:
                merged[key] = dict1[key]
        for key in dict2.keys():
            if key not in dict1.keys():
                merged[key] = dict2[key]
        return merged
    
    @staticmethod
    def choose_last(dict1: dict, dict2: dict) -> dict:
        """Merge two dictionaries, such that for each attribute x they share, its merged value is dict2[x].

        Args:
            dict1 (dict): A dictionary
            dict2 (dict): A dictionary

        Returns:
            dict: The merged dictionary
        """
        return MergePolicy._merge_dicts(dict1, dict2, lambda v1, v2: v2)
    
    @staticmethod
    def union(dict1: dict, dict2: dict) -> dict:
        """Merge two dictionaries, such that for each attributbe x they share, its merged value is a list that contains both dict1[x] and dict2[x].

        Args:
            dict1 (dict): A dictionary
            dict2 (dict): A dictionary

        Returns:
            dict: The merged dictionary.
        """
        return MergePolicy._merge_dicts(dict1, dict2, 
                                           lambda v1, v2: [v1, v2])

# %% ../nbs/05_rules.ipynb 9
_exception_msgs = {
    "clone_non_existing": lambda p_node, lhs_node: f"Node {p_node} clones an non-existing node {lhs_node}.",
    "clone_illegal_id": lambda p_node, copy_num: f"Node {p_node} clone id {copy_num} is illegal.",
    "p_bad_format": lambda p_node: f"Node {p_node} has a bad formatted name.",
    "p_not_in_lhs": lambda p_node: f"Node {p_node} in P does not exist in LHS.",
    "p_edge_not_in_lhs": lambda p_s, p_t: f"Edge {(p_s, p_t)} in P does not exist (and doesn't clone any edge) in LHS.",
    "rhs_illegal_name": lambda rhs_node: f"Node {rhs_node} merges at least one non-existing P node.",
    "rhs_not_in_p": lambda p_node: f"Node {p_node} in P does not exist in RHS, nor merges into an RHS node.",
    "add_attrs_in_p_node": lambda p_node: f"P node {p_node} cannot add attributes.",
    "add_attrs_in_p_edge": lambda s_copy, t_copy: f"P edge ({s_copy},{t_copy}) cannot add attributes.",
    "remove_attrs_in_rhs_node": lambda rhs_node: f"RHS node {rhs_node} cannot remove attributes.",
    "remove_attrs_in_rhs_edge": lambda s, t: f"RHS edge ({s},{t}) cannot remove attributes.",
    "attrs_in_cloned_node": lambda p_node: f"Cloned node {p_node} in P should not explicitly mention attributes",
    "attrs_in_cloned_edge": lambda s_copy, t_copy: f"Cloned edge ({s_copy},{t_copy}) in P should not explicitly mention attributes"
}

# %% ../nbs/05_rules.ipynb 10
class Rule:
    global _exception_msgs
    """A transformation rule, defined by 1-3 graphs:
    - LHS - defines the pattern to search for in the graph.
    - P - defines what parts to preserve (and also defines clones).
    - RHS - defines what parts to add (and also defines merges).
    """
    # TODO: add collections_mapping member of the class # Collections Feature
    def __init__(self, lhs: DiGraph, p: DiGraph = None, rhs: DiGraph = None, merge_policy = MergePolicy.choose_last):
        self.lhs = lhs
        self.p = p if p else self.lhs.copy()
        self.rhs = rhs if rhs else self.p.copy()
        #self.collection_mapping = collection_mapping # Collections Feature
        self.merge_policy = merge_policy

        self._p_to_lhs, self._p_to_rhs = {}, {}
        self._merge_sym, self._clone_sym = '&', '*'
        self._create_p_lhs_hom()
        self._create_p_rhs_hom()

        self._rev_p_lhs = self._reversed_dictionary(self._p_to_lhs)
        self._rev_p_rhs = self._reversed_dictionary(self._p_to_rhs)
        self._validate_rule()

    # Utils
    def _create_p_lhs_hom(self):
        """Construct the homomorphism from P to LHS based on the rule.
        Handles cloned nodes.
        """
        for p_node in self.p.nodes():
            # If the p_node contains the cloning symbol, then it's a clone. Extract the clone it denotes (if any)
            if self._clone_sym in str(p_node):
                if len(str(p_node).split(self._clone_sym)) == 2:
                    lhs_node, copy_num = str(p_node).split(self._clone_sym)
                    # Clones must have the format "{node}*{copy_num}" where node is in LHS, copy_num is a number
                    if lhs_node not in self.lhs.nodes():
                        raise GraphRewriteException(_exception_msgs["clone_non_existing"](p_node, lhs_node))
                    elif not copy_num.isnumeric():
                        raise GraphRewriteException(_exception_msgs["clone_illegal_id"](p_node, copy_num))
                    else:
                        # Map the clone p node to the cloned lhs node
                        self._p_to_lhs[p_node] = lhs_node
                # Clones must have the format "{node}*{copy_num}"
                else:
                    raise GraphRewriteException(_exception_msgs["p_bad_format"](p_node))
            # Else, p_node is a preservation of an lhs_node with the same name
            elif p_node in self.lhs.nodes():
                self._p_to_lhs[p_node] = p_node
            # If it's neither, then the p_node is illegal (does not preserve / clone)
            else:
                raise GraphRewriteException(_exception_msgs["p_not_in_lhs"](p_node))
            # TODO: map a collection node in p to lhs # Collections Feature
            '''
            elif p_node in collection_mapping.keys():
                for i in range(len(collection_mapping[p_node].items))
                    self._p_to_lhs[p_node+"_"+i] = p_node+"_"+i
            '''

    def _create_p_rhs_hom(self):
        """Construct the homomorphism from P to RHS based on the rule.
        Handles merged nodes.
        """
        for rhs_node in self.rhs.nodes():
            # If the rhs_node has the merging symbol, then it's a merge. Extract the P nodes it merges (if any)
            if self._merge_sym in str(rhs_node):
                # Merged node must have the format "{}&{}&...&{}" where each argument is a P node
                if len(str(rhs_node).split(self._merge_sym)) > 1:
                    p_nodes = str(rhs_node).split(self._merge_sym)
                    # Check that the merge refrences only existing p nodes
                    if all([p_node in self.p.nodes() for p_node in p_nodes]):
                        # If so, map each p_node to the new merged rhs node
                        for p_node in p_nodes:
                            self._p_to_rhs[p_node] = rhs_node
                            # TODO: if it's a node that represents a collection (is in collection_mapping.keys()) add all nodes that it represents
                            # (Same as in lhs) # Collections Feature
                    else:
                        raise GraphRewriteException(_exception_msgs["rhs_illegal_name"](rhs_node))
        for p_node in self.p.nodes():
            # Every node in P must be mapped to its preserved RHS node, or to the node that merges it (this case is already handled at this point)
            if p_node not in self._p_to_rhs.keys():
                if p_node in self.rhs.nodes():
                    self._p_to_rhs[p_node] = p_node
                else:
                    raise GraphRewriteException(_exception_msgs["rhs_not_in_p"](p_node))

    def _reversed_dictionary(self, dictionary: dict) -> dict[Any, set]:
        """Given a dictionary, return a dictionary which maps every
        value from the original dictionary to the set of keys 
        that are mapped to it.

        E.g., for {1: 'a', 2: 'a', 3: 'b'}, the reversing function
        returns {'a': {1,2}, 'b': {3}}.

        Args:
            dictionary (dict): A dictionary to reverse

        Returns:
            dict[Any, set]: A reversed dictionary as described
        """
        rev_dict: dict[Any, set] = {}
        for key, value in dictionary.items():
            if value not in rev_dict:
                rev_dict[value] = set()
            rev_dict[value].add(key)
        return rev_dict

    def _dict_difference(self, target: dict, other: dict) -> dict:
        """Given two dictionaries, create a new dictionary which "subtracts" the other dictionary from the target one:
        For each key in target, if it does not appear in the other dictionary, or appears there with a different value,
        then we map the key to the target value in the new dictionary. Otherwise, the key is not included in the new dictionary.

        Args:
            target (dict): A dictionary
            other (dict): A dictionary to subtract from target

        Returns:
            dict: The difference dictionary as explained
        """
        new_dict = {}
        for key in target:
            if key in other and target[key] != other[key]:
                new_dict[key] = target[key]
            elif key not in other:
                new_dict[key] = target[key]
        return new_dict

    def _validate_lhs_p(self):
        """Validates the LHS->P homomorphism, and raises appropriate exceptions if it's invalid.
        """

        # Nodes in P do NOT add attributes that aren't in the corresponding LHS node(s).
        for node_lhs in self.lhs.nodes():
            lhs_attrs = set(self.lhs.nodes(data=True)[node_lhs].keys())
            p_copies = self._rev_p_lhs.get(node_lhs, set())
            for node_p in p_copies:
                p_attrs = set(self.p.nodes(data=True)[node_p].keys())
                if not p_attrs.issubset(lhs_attrs):
                    raise GraphRewriteException(_exception_msgs["add_attrs_in_p_node"](node_p))
        
        # Edges in P do NOT add attributes that aren't in the corresponding LHS edge(s).
        for s, t in self.lhs.edges():
            rhs_attrs = set(self.lhs.get_edge_data(s, t).keys())
            s_copies, t_copies = self._rev_p_lhs.get(s, set()), self._rev_p_lhs.get(t, set())
            for s_copy in s_copies:
                for t_copy in t_copies:
                    # For each "clone of edge (s, t)" that is in P
                    if (s_copy, t_copy) in self.p.edges():
                        p_attrs = set(self.p.get_edge_data(s_copy, t_copy).keys())
                        if not p_attrs.issubset(rhs_attrs):
                            raise GraphRewriteException(_exception_msgs["add_attrs_in_p_edge"](s_copy, t_copy))
                        
        # Edges in P must have a corresponding LHS edge #TODO: or a corresponding edge collection # Collections Featue
        for p_s, p_t in self.p.edges():
            if (self._p_to_lhs[p_s], self._p_to_lhs[p_t]) not in self.lhs.edges():
                raise GraphRewriteException(_exception_msgs["p_edge_not_in_lhs"](p_s, p_t))
        
        #TODO: Add checks that nodes and edges in collections do not add attributes # Collections Feature

    def _validate_rhs_p(self):
        """Validates the RHS->P homomorphism, and raises appropriate exceptions if it's invalid.
        """

        # Nodes in RHS do NOT remove attributes that are in the corresponding P node(s).
        # Note that we ignore merged nodes here (which follow this rule automatically).
        for node_rhs in self.rhs.nodes():
            if node_rhs not in self.nodes_to_merge().keys():
                rhs_attrs = set(self.rhs.nodes(data=True)[node_rhs].keys())
                p_origins = self._rev_p_rhs.get(node_rhs, set())
                for node_p in p_origins:
                    p_attrs = set(self.p.nodes(data=True)[node_p].keys())
                    if not p_attrs.issubset(rhs_attrs):
                        raise GraphRewriteException(_exception_msgs["remove_attrs_in_rhs_node"](node_rhs))
        
        # Edges in RHS do NOT remove attributes that are in the corresponding P edge(s).
        # Note that we ignore edges created by a merge here (they follow this rule automatically).
        for s, t in self.rhs.edges():
            if s not in self.nodes_to_merge().keys() and t not in self.nodes_to_merge().keys():
                rhs_attrs = set(self.rhs.get_edge_data(s, t).keys())
                s_origins, t_origins = self._rev_p_rhs.get(s, set()), self._rev_p_rhs.get(t, set())
                for s_origin in s_origins:
                    for t_origin in t_origins:
                        if (s_origin, t_origin) in self.p.edges():
                            origin_attrs = set(self.p.get_edge_data(s_origin, t_origin).keys())
                            if not origin_attrs.issubset(rhs_attrs):
                                raise GraphRewriteException(_exception_msgs["remove_attrs_in_rhs_edge"](s,t))

        #TODO: Add checks that nodes and edges in collections do not remove attributes # Collections Feature

    def _validate_rule(self):
        """Validates the rule - that is, checking that the homomorphisms are valid, and that clones mentioned in the rule
        are valid (if any exist).
        """

        self._validate_lhs_p()
        self._validate_rhs_p()
        
        clones = {item for clones_list in self.nodes_to_clone().values() for item in clones_list}
        # validate cloned nodes in P have no attributes mentioned (all attributes are copied automatically)
        for clone in clones:
            if self.p.nodes(data=True)[clone] != {}:
                raise GraphRewriteException(_exception_msgs["attrs_in_cloned_node"](clone))
        
        # validate cloned edges in P (edges with cloned endpoint) have no attributes mentioned
        for s, t, attrs in self.p.edges(data=True):
            if (s in clones or t in clones) and attrs != {}:
                raise GraphRewriteException(_exception_msgs["attrs_in_cloned_edge"](s, t))

    def _merge_node_attrs(self, rhs_node: NodeName, p_origins: list[NodeName]) -> dict:
        """Given a node in RHS that is a copy / a merge of one or more nodes in P,
        and the P nodes which it copies / merges, returns the dictionary of new attributes
        added to the merged node in RHS (That is, not including the attributes which stem from the merge, other than merged attributes which were overriden in RHS).

        Args:
            rhs_node (NodeName): A node in RHS
            p_origins (list[NodeName]): A list of P nodes which rhs_node merges.

        Returns:
            dict: A dictionary of added attributes (keys and values) of the merged RHS node.
        """
        merge_rhs_attrs = {}
        for p_origin in p_origins:
            new_rhs_attrs = self._dict_difference(self.rhs.nodes[rhs_node], self.p.nodes[p_origin])
            merge_rhs_attrs = self.merge_policy(merge_rhs_attrs, new_rhs_attrs)
        return merge_rhs_attrs

    def _merge_edge_attrs(self, rhs_edge: EdgeName, s_origins: list[NodeName], t_origins: list[NodeName]) -> dict:
        """Given an edge in RHS that is possibly a copy / a merge of one or more edges,
        and the copies / merges of both its endpoints, returns the dictionary of new attributes
        added to the merged edge in RHS (That is, not including the attributes which stem from the merge, other than merged attributes which were overriden in RHS).

        Args:
            rhs_edge (EdgeName): An edge in RHS
            s_origins (list[NodeName]): A list of P nodes which the source endpoint of the edge merges.
            t_origins (list[NodeName]): A list of P nodes which the target endpoint of the edge merges.

        Returns:
            dict: A dictionary of added attributes (keys and values) of the merged RHS edge.
        """
        merge_rhs_attrs = {}
        for s_origin in s_origins:
            for t_origin in t_origins:
                if (s_origin, t_origin) in self.p.edges():
                    new_rhs_attrs = self._dict_difference(
                        self.rhs.get_edge_data(*rhs_edge),
                        self.p.get_edge_data(s_origin, t_origin)
                    )
                    merge_rhs_attrs = self.merge_policy(merge_rhs_attrs, new_rhs_attrs)
        return merge_rhs_attrs

    # The following functions are presented in the order of transformation.
    def nodes_to_clone(self) -> dict[NodeName, set[NodeName]]:
        """Find all LHS nodes that should be cloned in P, and for each node, find all its P clones.

        Returns:
            dict[NodeName, set[NodeName]]:
                A dictionary which maps each cloned node in LHS to a set
                of all nodes in P which are its clones.
        """

        # Find all LHS nodes which are mapped by more than one node in P (in the P->LHS Hom.)
        return {lhs_node: self._rev_p_lhs[lhs_node] for lhs_node in self.lhs.nodes() \
                            if len(self._rev_p_lhs.get(lhs_node, set())) > 1}
        # TODO: also add node Collections to clone to the set by using rev_p_lhs # Collections Feature



    def nodes_to_remove(self) -> set[NodeName]:
        """Find all LHS nodes that should be removed.

        Returns:
            set[NodeName]: Nodes in LHS which should be removed.
        """

        # Find all LHS nodes which are not mapped by any node in P (in the P->LHS Hom.)
        return {lhs_node for lhs_node in self.lhs.nodes() if len(self._rev_p_lhs.get(lhs_node, set())) == 0}
        # TODO: also add node Collections to remove to the set by using rev_p_lhs # Collections Feature

    def edges_to_remove(self) -> set[EdgeName]:
        """Find all P edges that should be removed.

        Note: Does not include edges which one of their endpoints was removed by the rule,
        as during transformation, we begin by removing all removed nodes along with the connected edges.

        Returns:
            set[EdgeName]: Edges in P which should be removed.
        """
        edges_to_remove = set()
        for s, t in self.lhs.edges():
            # If one of the edge endpoints was removed, the edge was removed automatically so we skip it here
            if s not in self.nodes_to_remove() and t not in self.nodes_to_remove():
                s_copies, t_copies = self._rev_p_lhs.get(s, set()), self._rev_p_lhs.get(t, set())
                for s_copy in s_copies:
                    for t_copy in t_copies:
                        # For each "clone of edge (s,t)" that shouldn't be in P, remove it
                        if (s_copy, t_copy) not in self.p.edges():
                            edges_to_remove.add((s_copy, t_copy))
        # TODO: also add edge Collections to remove to the set by using rev_p_lhs # Collections Feature
        return edges_to_remove

    def node_attrs_to_remove(self) -> dict[NodeName, set]:
        """For each P node, find all attributes of its corresponding LHS node
        which should be removed from it in P.

        Returns:
            dict[NodeName, set]: A dictionary from P nodes to attributes that should be
                removed from their corresponding LHS nodes.
        """
        attrs_to_remove = {}
        for node_lhs in self.lhs.nodes():
            if node_lhs not in self.nodes_to_clone().keys(): # cloned nodes do not remove attrs
                p_copies = self._rev_p_lhs.get(node_lhs, set())
                for node_p in p_copies:
                    # Find all attributes that are in the LHS node but not in the new P node
                    diff_attrs = set(self._dict_difference(
                        self.lhs.nodes[node_lhs],
                        self.p.nodes[node_p]
                    ).keys())
                    if len(diff_attrs) != 0:
                        # Remove all such attributes from the P node
                        attrs_to_remove[node_p] = diff_attrs
        # TODO: also add node Collections attributes to remove to the set by using rev_p_lhs # Collections Feature
        return attrs_to_remove

    def edge_attrs_to_remove(self) -> dict[EdgeName, set]:
        """For each P edge, find all attributes of its corresponding LHS edge
        which should be removed from it in P.

        Returns:
            dict[EdgeName, set]: A dictionary from P edges to attributes that should be
                removed from their corresponding LHS edges.
        """
        attrs_to_remove = {}
        for s, t in self.lhs.edges():
            s_copies, t_copies = self._rev_p_lhs.get(s, set()), self._rev_p_lhs.get(t, set())
            for s_copy in s_copies:
                for t_copy in t_copies:
                    # For each "clone of edge (s, t)" that is in P
                    if (s_copy, t_copy) in self.p.edges():
                        diff_attrs = set(self._dict_difference(
                            self.lhs.get_edge_data(s,t),
                            self.p.get_edge_data(s_copy, t_copy)
                        ).keys())
                        if len(diff_attrs) != 0:
                            # Remove all such attributes
                            attrs_to_remove[(s_copy, t_copy)] = diff_attrs
        # TODO: also add edge Collections attributes to remove to the set by using rev_p_lhs# Collections Feature
        return attrs_to_remove

    def nodes_to_merge(self) -> dict[NodeName, set[NodeName]]:
        """Find all RHS nodes which are a merge of nodes in P, and for each node, find all P nodes that merge into it.

        Returns:
            dict[NodeName, set[NodeName]]: 
                A dictionary which maps each node in RHS that is a merge of P nodes,
                to a set of nodes in P which it merges.
        """

        # Find all RHS nodes that are mapped by more than one node in P (in the P->RHS Hom.)
        return {rhs_node: self._rev_p_rhs[rhs_node] for rhs_node in self.rhs.nodes() \
                            if len(self._rev_p_rhs.get(rhs_node, set())) > 1}

    def nodes_to_add(self) -> set[NodeName]:
        """Find all RHS nodes which should be added.

        Note: Does not include nodes in RHS that are created as a merge of P nodes.

        Returns:
            set[NodeName]: Nodes which should be added to RHS.
        """

        # Find all RHS nodes which are not mapped by any node in P (in the P->RHS Hom.)
        return {rhs_node for rhs_node in self.rhs.nodes() if len(self._rev_p_rhs.get(rhs_node, set())) == 0}

    def edges_to_add(self) -> set[EdgeName]:
        """Find all RHS edges that should be added. 

        Note: Does not include edges added to merged nodes.

        Returns:
            set[EdgeName]: Edges which should be added to RHS.
        """
        edges_to_add = set()
        for s, t in self.rhs.edges():
            # New edges from at least one new node (not including merged nodes)
            if s in self.nodes_to_add() or t in self.nodes_to_add():
                edges_to_add.add((s,t)) # surely a new edge
            else:
                s_origins, t_origins = self._rev_p_rhs.get(s, set()), self._rev_p_rhs.get(t, set())
                # New edges from existing P nodes
                if all([(s_origin, t_origin) not in self.p.edges() for s_origin in s_origins for t_origin in t_origins]):
                    edges_to_add.add((s,t))
        #TODO: if one of the edge's nodes is a collection - add the edge to each of the nodes in the collections
        return edges_to_add

    def node_attrs_to_add(self) -> dict[NodeName, dict]:
        """For each RHS node, find all attributes (and values) of its corresponding P node(s)
        which should be added to the RHS node.
        
        Returns:
            dict[NodeName, dict]: A dictionary that maps RHS nodes to their added attributes and values.
        """
        attrs_to_add = {}
        for node_rhs in self.rhs.nodes():
            if node_rhs in self.nodes_to_add():
                rhs_attrs = self.rhs.nodes(data=True)[node_rhs]
                if len(rhs_attrs) != 0:
                    attrs_to_add[node_rhs] = rhs_attrs
            else:
                p_origins = self._rev_p_rhs.get(node_rhs, set())
                merged_p_attrs = self._merge_node_attrs(node_rhs, p_origins)
                if len(merged_p_attrs) != 0:
                    attrs_to_add[node_rhs] = merged_p_attrs
        # TODO: also add node Collections attributes to add to the set by using rev_p_rhs # Collections Feature
        return attrs_to_add

    def edge_attrs_to_add(self) -> dict[EdgeName, dict]:
        """For each RHS edge, find all attributes (and values) of its corresponding P edge(s)
        which should be added to the RHS edge.

        Returns:
            dict[EdgeName, dict]: A dictionary that maps RHS edges to their added attributes and values.
        """
        attrs_to_add = {}
        for s, t in self.rhs.edges():
            if s in self.nodes_to_add() or t in self.nodes_to_add():
                rhs_attrs = self.rhs.get_edge_data(s, t)
                if len(rhs_attrs) != 0:
                    attrs_to_add[(s, t)] = rhs_attrs
            else:
                s_origins, t_origins = self._rev_p_rhs.get(s, set()), self._rev_p_rhs.get(t, set())
                merged_p_attrs = self._merge_edge_attrs((s, t), s_origins, t_origins)
                if len(merged_p_attrs) != 0:
                    attrs_to_add[(s, t)] = merged_p_attrs
        #TODO: also add edge Collections attributes to add to the set by using rev_p_lhs# Collections Feature
        return attrs_to_add

