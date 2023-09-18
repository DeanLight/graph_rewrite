# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/04_p_rhs_parsing.ipynb.

# %% auto 0
__all__ = ['p_parser', 'rhs_parser', 'rhs_to_graph', 'p_to_graph']

# %% ../nbs/04_p_rhs_parsing.ipynb 4
from lark import Lark
from lark import UnexpectedCharacters, UnexpectedToken
import networkx as nx
from .match_class import Match
from .core import GraphRewriteException
from .core import _create_graph, _plot_graph, _graphs_equal
from .lhs import RenderFunc, graphRewriteTransformer

# %% ../nbs/04_p_rhs_parsing.ipynb 6
p_parser = Lark(r"""
    %import common.WS -> WS
    %ignore WS

    NAMED_VERTEX: /[_a-zA-Z0-9\*]+/
    ATTR_NAME: /[_a-zA-Z0-9]+/
    INDEX: /[0-9]+/
        
    attribute: ATTR_NAME
    attributes: "[" attribute ("," attribute)* "]"

    connection: ["-" attributes]"->"
    
    index_vertex: NAMED_VERTEX "<" INDEX ("," INDEX)* ">"

    vertex: NAMED_VERTEX [attributes]
    | index_vertex [attributes]

    empty:
    pattern: vertex (connection vertex)*
    patterns: pattern (";" pattern)* | empty

    """, parser="lalr", start='patterns' , debug=True)

# %% ../nbs/04_p_rhs_parsing.ipynb 8
rhs_parser = Lark(r"""
    %import common.INT -> INT 
    %import common.FLOAT -> FLOAT
    %import common.ESCAPED_STRING -> STRING
    %import common.WS -> WS
    %ignore WS

    NAMED_VERTEX: /[_a-zA-Z0-9\*&]+/
    ATTR_NAME: /[_a-zA-Z0-9]+/
    TYPE:  "int" | "string"
    BOOLEAN: "True" | "False"
    NATURAL_NUMBER: /[1-9][0-9]*/
    INDEX: /[0-9]+/
    USER_VALUE: /\{\{[^[\]{};=]*\}\}/

    value: FLOAT | INT | BOOLEAN | USER_VALUE | STRING

    attribute: ATTR_NAME [":" TYPE] ["=" value]
    attributes: "[" attribute ("," attribute)* "]"

    connection: ["-" attributes]"->"
    
    index_vertex: NAMED_VERTEX "<" INDEX ("," INDEX)* ">"

    vertex: NAMED_VERTEX [attributes]
    | index_vertex [attributes]

    empty:
    pattern: vertex (connection vertex)*
    patterns: pattern (";" pattern)* | empty

    """, parser="lalr", start='patterns' , debug=True)

# %% ../nbs/04_p_rhs_parsing.ipynb 10
def rhs_to_graph(rhs: str, match: Match = None, render_funcs: dict[str, RenderFunc] = {}):
    """Given an RHS pattern, a match caught by the LHS, and functions that represent the values of the 
    possible placeholders in the pattern, return the directed graph represented by the pattern, 
    with rendered attribute values according to the functions and the match.

    Args:
        rhs (string): A string in lhs format 
        match (Match): a match object caught by the matcher module
        render_funcs (dict[str, RenderFunc]): A dictionary supplied by the user 
                                              indicating which value every placeholder should be rendered with.

    Returns:
        DiGraph: a networkx graph that is the graph represented by the pattern, with rendered attribute values.
    """
    try:
        tree = rhs_parser.parse(rhs)
        rhs_graph, _ = graphRewriteTransformer(component="RHS", match=match, render_funcs=render_funcs).transform(tree)                
        return rhs_graph
    except (BaseException, UnexpectedCharacters, UnexpectedToken) as e:
        raise GraphRewriteException('Unable to convert RHS: {}'.format(e))

# %% ../nbs/04_p_rhs_parsing.ipynb 11
def p_to_graph(p: str):
    """Given an P pattern, return the directed graph represented by the pattern.

    Args:
        p (string): A string in lhs format 

    Returns:
        DiGraph: a networkx graph that is the graph represented by the pattern.
    """
    try:
        tree = p_parser.parse(p)
        p_graph, _ = graphRewriteTransformer(component="P").transform(tree)                
        return p_graph
    except (BaseException, UnexpectedCharacters, UnexpectedToken) as e:
        raise GraphRewriteException('Unable to convert P: {}'.format(e))