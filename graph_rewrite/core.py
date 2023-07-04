# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_core.ipynb.

# %% auto 0
__all__ = ['NodeName', 'EdgeName', 'plot_consts', 'GraphRewriteException']

# %% ../nbs/00_core.ipynb 4
from networkx import DiGraph, planar_layout, spring_layout, draw_networkx_nodes, draw_networkx_labels, draw_networkx_edges
import matplotlib.pyplot as plt
from typing import *

# %% ../nbs/00_core.ipynb 6
class GraphRewriteException(Exception):
    """Exception class for the graph_rewrite library."""
    def __init__(self, msg: str):
        self.message = msg
        super().__init__(msg)
    pass

# %% ../nbs/00_core.ipynb 9
NodeName = str
# When defining an edge, the first node is the source and the second is the target (as we use directed graphs).
EdgeName = Tuple[NodeName, NodeName]

# %% ../nbs/00_core.ipynb 11
def _create_graph(nodes: list[Union[NodeName, Tuple[NodeName, dict]]], edges: list[Union[EdgeName, Tuple[NodeName, NodeName, dict]]]) -> DiGraph:
    """Construct a directed graph (NetworkX DiGraph) out of lists of nodes and edges.

    Args:
        nodes (list[Union[NodeName, Tuple[NodeName, dict]]]): 
            a list of node names (with or without attributes). e.g., ['A', 'B', (1, {'attr': 5}), 2].
        edges (list[Union[EdgeName, Tuple[NodeName, NodeName, dict]]]):
            a list of edges, each defined by a tuple of two node names (source, target), perhaps with attributes added.
            e.g., [('A','B'), (1,'A', {'attr': 5})].

    Returns:
        DiGraph: the newly constructed DiGraph.
    """
    g = DiGraph()
    g.add_nodes_from(nodes)
    g.add_edges_from(edges)
    return g

# %% ../nbs/00_core.ipynb 13
plot_consts = {
    "node_size": 300,
    "node_color": 'g',
    # Highlighted nodes can have different colors
    "hl_node_color": 'r',

    "font_size": 10,
    "font_color": 'w',

    "arrow_size": 10,
    "edge_color": 'k',
    "edge_width": 1,
    # Highlighted edges can have different colors
    "hl_edge_color": 'r',
    "hl_edge_width": 2,

    # The plotter has some optional layouting modes, we choose one here
    "layouting_method": planar_layout
}

# %% ../nbs/00_core.ipynb 15
def _plot_graph(g: DiGraph, hl_nodes: set[NodeName] = set(), hl_edges: set[EdgeName] = set()):
    """Plot a graph, and potentially highlight certain nodes and edges.

    Args:
        g (DiGraph): a graph to plot
        hl_nodes (set[NodeName], optional): set of node names to highlight. Defaults to set().
        hl_edges (set[EdgeName], optional): set of edge names to highlight. Defaults to set().
    """
    global plot_consts

    # Seperate highlighted nodes and edges, remove if doesn't exist in the graph g
    hl_nodes = [node for node in g.nodes() if node in hl_nodes]
    non_hl_nodes = [node for node in g.nodes() if node not in hl_nodes]
    hl_edges = [edge for edge in g.edges() if edge in hl_edges]
    non_hl_edges = [edge for edge in g.edges() if edge not in hl_edges]

    # plotting
    for layout in [plot_consts["layouting_method"], spring_layout]:
        try:
            pos = layout(g)
            draw_networkx_nodes(g, pos, nodelist=non_hl_nodes, node_size=plot_consts["node_size"], 
                                node_color=plot_consts["node_color"])
            draw_networkx_nodes(g, pos, nodelist=hl_nodes, node_size=plot_consts["node_size"], 
                                node_color=plot_consts["hl_node_color"])
            draw_networkx_labels(g, pos, font_size=plot_consts["font_size"], font_color=plot_consts["font_color"])
            draw_networkx_edges(g, pos, edgelist=non_hl_edges, arrowsize=plot_consts["arrow_size"], 
                                node_size=plot_consts["node_size"], edge_color=plot_consts["edge_color"], width=plot_consts["edge_width"])
            draw_networkx_edges(g, pos, edgelist=hl_edges, arrowsize=plot_consts["arrow_size"], node_size=plot_consts["node_size"],
                                 edge_color=plot_consts["hl_edge_color"], width=plot_consts["hl_edge_width"])
            return
        except:
            print("Graph isn't planar, priniting in spring layout mode.")
