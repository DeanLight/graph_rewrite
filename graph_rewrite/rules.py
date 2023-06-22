# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/07_rules.ipynb.

# %% auto 0
__all__ = ['Rule']

# %% ../nbs/07_rules.ipynb 4
from networkx import DiGraph
from .result_set import *
from typing import *
from .core import GraphRewriteException

# %% ../nbs/07_rules.ipynb 8
class Rule:
    def __init__(self, lhs: DiGraph, rhs: DiGraph = DiGraph(), p: DiGraph = DiGraph()):
        self.lhs = lhs
        self.rhs = rhs
        self.p = p
        

        self.p_to_lhs, self.p_to_rhs = {}, {}
        self.merge_sym, self.clone_sym = '&', '*'
        self._create_hom()



    def _create_hom(self):
        """
        Create a homomorphism from g1 to g2 as identity functions.
        That is, preserve everything / don't clone / don't merge.
        """
        # p->lhs - check for clones
        # for p_node in self.p.nodes():
        #     node_split = p_node.split(self.clone_sym)

        #     # Check if the p-node is a clone of a lhs-node
        #     if len(node_split) == 2:
        #         cloned_lhs_node = node_split[0]
        #         if cloned_lhs_node in self.lhs.nodes():
        #             self.p_to_lhs[p_node] = cloned_lhs_node
        #         else:
        #             raise GraphRewriteException(
        #                 f"In P, node \"{p_node}\" suggests a clone of a non-existing LHS node \"{cloned_lhs_node}\""
        #             )

        #     # 
        #     elif p_node in self.lhs.nodes():
                
        

        # hom = {}
        # for node in g1.nodes():
        #     if node in g2.nodes():
        #         hom[node] = node # identity
        # return hom

    def nodes_to_add(self):
        pass

    def edges_to_add(self):
        pass

    def nodes_to_remove(self):
        pass

    def edges_to_remove(self):
        pass

    def nodes_to_clone(self):
        pass

    def nodes_to_merge(self):
        pass
