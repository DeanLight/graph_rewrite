# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_lhs_parsing.ipynb.

# %% auto 0
__all__ = ['lhs_parser', 'RenderFunc', 'cnt', 'graphRewriteTransformer', 'lhs_to_graph']

# %% ../nbs/01_lhs_parsing.ipynb 4
import copy
from collections.abc import Callable
import networkx as nx
from lark import Transformer, Lark
from lark import UnexpectedCharacters, UnexpectedToken
from .match_class import Match
from .core import GraphRewriteException
from .core import _create_graph, _plot_graph, _graphs_equal

# %% ../nbs/01_lhs_parsing.ipynb 6
lhs_parser = Lark(r"""
    %import common.INT -> INT 
    %import common.FLOAT -> FLOAT
    %import common.ESCAPED_STRING -> STRING
    %import common.WS -> WS
    %ignore WS

    NAMED_VERTEX: /[a-zA-Z0-9]+/
    ANONYMUS: "_"
    ATTR_NAME: /[a-zA-Z0-9]+/
    TYPE:  "int" | "string"
    BOOLEAN: "True" | "False"
    NATURAL_NUMBER: /[1-9][0-9]*/
    INDEX: /[0-9]+/

    value: FLOAT | INT | BOOLEAN | STRING

    attribute: ATTR_NAME [":" TYPE] ["=" value]
    attributes: "[" attribute ("," attribute)* "]"

    multi_connection: "-" NATURAL_NUMBER [attributes] "->" 
    connection: ["-" attributes]"->"
              | multi_connection
    
    index_vertex: NAMED_VERTEX "<" INDEX ("," INDEX)* ">"

    vertex: NAMED_VERTEX [attributes]
    | index_vertex [attributes]
    | ANONYMUS [attributes]

    pattern: vertex (connection vertex)*
    patterns: pattern (";" pattern)*

    """, parser="lalr", start='patterns' , debug=True)

# multi_connection: "-" NATURAL_NUMBER "+" [attributes] "->"  - setting for the "-num+->" feature

# %% ../nbs/01_lhs_parsing.ipynb 8
RenderFunc = Callable[[Match], any] # type of a function to render a parameter

# %% ../nbs/01_lhs_parsing.ipynb 9
cnt:int = 0 # unique id for anonymous vertices
class graphRewriteTransformer(Transformer):
    def __init__(self, visit_tokens: bool = True, component: str = "LHS", match: Match = None, render_funcs: dict[str, RenderFunc] = {}) -> None:
        super().__init__(visit_tokens)
        # general
        self.component = component
        # RHS parameters
        self.match = match
        self.render_funcs = render_funcs
        # LHS parameters
        self.constraints = {}
        self.cnt = 0

    def STRING(self, arg):
        # remove " "
        return arg[1:-1] 
    
    def BOOLEAN(self, arg):
        return bool(arg)
    
    def INT(self, arg):
        # can be negative
        return int(arg)
    
    def FLOAT(self, arg):
        return float(arg)
    
    def NATURAL_NUMBER(self, number): 
        # represents number of duplications
        return int(number)
    
    def USER_VALUE(self, arg):
        # get the variable name
        variable = arg[2:-2]
        # extract the actual value supplied by the user - can be of any type.
        return self.render_funcs[variable](self.match) 
    
    def value(self, args): 
        # one argument encased in a list
        return args[0]
    
    def attribute(self, args): 
        # if an optional token was not parsed, None is placed in the parse tree.
        attr_name, type, value = args
        # pass a tuple of attr_name, required type, required value.
        return (attr_name, type, value)
    
    def attributes(self, attributes): # a list of triples 
        # return a packed list of the attribute names.
        attr_names, constraints = {}, {}
        for attribute in attributes:
            # will be added to the graph itself
            attr_name, type, value = attribute
            if self.component == "LHS":
                attr_names[str(attr_name)] = None 
                # will be added to the condition function
                constraints[str(attr_name)] = (type, value) 
            else:
                attr_names[str(attr_name)] = value

        return (attr_names, constraints)

    def multi_connection(self, args): # +
        # return the list of attributes(strings), add a special attribute to denote number of duplications.
        number, attributes = args
        if attributes == None:
            attributes = ({},{})
        # add a special atrribute to handle duplications during construction
        attributes[0]["$dup"] = number 
        return attributes

    def connection(self, args): 
        # (tuple of dicts: attributes, constraints. attributes is of the form: attribute -> val)
        attributes = args[0]
        if attributes == None:
            attributes = ({},{})
        # add a special atrribute to handle duplications during construction
        attributes[0]["$dup"] = 1
        return (attributes, True)

    def ANONYMUS(self, _): #
        # return a dedicated name for anonymus (string), and an empty indices list.
        x = "_" + str(self.cnt)
        self.cnt += 1
        return (x, [])

    def index_vertex(self, args):
        # return the main name of the vertex, and a list of the indices specified.
        main_name_tup, *numbers = args #numbers is a list
        return (main_name_tup[0], list(numbers))
    
    def NAMED_VERTEX(self, name):
        # return the main name of the vertex, and an empty indices list.
        return (str(name), [])

    def vertex(self, args): # (vertex_tuple: tuple, attributes: list)
        # attributes is a empty list/ a list containing a tuple: (names dict, constraints dict)
        vertex_tuple, *attributes = args 
        name, indices_list = vertex_tuple

        # create new name
        indices = ",".join([str(num) for num in indices_list])
        if len(indices) == 0:
            new_name = str(name)
        else:
            new_name =  name + "<" + indices + ">" 

        # no attributes to handle
        if attributes[0] == None:
            return (new_name, {})
        
        # now that we have the vertex name we add the attribute constraints:
        # vertices may appear multiple times in LHS thus we unite the constraints. We assume there cannot be contradicting constraints.
        attribute_names, constraints = attributes[0] 
        # the second element of the tuple is the constraints dict: attr_name -> (value,type)
        if self.component == "LHS":
            if new_name not in self.constraints.keys():
                self.constraints[new_name] = {}
            self.constraints[new_name] = self.constraints[new_name] | constraints 
        return (new_name, attribute_names)

    def pattern(self, args):
        # 1) unpack lists of vertices and connections.
        vertex, *rest = args
        conn, vertices = list(rest)[::2], list(rest)[1::2]
        vertices.insert(0,vertex)
        # 2) create a networkX graph:
            # Future feature: if there is a special attribute with TRUE (deterministic), dumplicate the connection $dup times.
        G = nx.DiGraph()

        # simplified vertion - ignore duplications
        G.add_nodes_from(vertices)
        edge_list = []
        for i,edge in enumerate(conn):
            # for now the duplication feature is not included so we remove the $dup attribute
            # we handeled None in the connection rule.
            attribute_names, constraints = edge[0]
            attribute_names.pop("$dup", 0)
            # ignore edge[1] - determinism flag. edge[0] is the tuple of dicts of attributes.
            vertex_name_pos = 0 # each item in vertices is a tuple (vertex_name, attrs)
            edge_list.append((vertices[i][vertex_name_pos], vertices[i+1][vertex_name_pos], attribute_names)) 

            # add constraints - we assume an edge only appears once in LHS
            if self.component == "LHS":
                filtered_cons = dict(filter(lambda tup: not tup[1] == (None, None), constraints.items()))
                # check if filtered_cons is not empty - there are concrete constraints
                if filtered_cons: 
                    self.constraints[str(vertices[i][vertex_name_pos]) + "->" + str(vertices[i+1][vertex_name_pos])] = filtered_cons

        # more complex vertion - duplications
        # create a recursive function that adds the vertices and edges, 
        # that calls itself by the number of duplications on each level.

        G.add_edges_from(edge_list)
        return G

    def patterns(self, args):
        g, *graphs = args
        graphs.insert(0,g)
        # unite all the patterns into a single graph
        G = nx.DiGraph()

        # dict of dicts (node_name -> attribute -> None/someValue)
        combined_attributes = dict() 
        new_nodes = []
        new_edges = []
        for graph in graphs:
            for node in graph.nodes:
                if node not in combined_attributes.keys():
                    combined_attributes[node] = {}
                combined_attributes[node] = combined_attributes[node] | graph.nodes.data()[node]
                #unite the dicts for each
                new_nodes.append(node) 
            for edge in graph.edges:
                # we assumed edges cannot appear more than once in LHS
                combined_attributes[edge[0] + "->" + edge[1]] = graph.edges[edge[0],edge[1]]
                new_edges.append(edge)
        # filtered_attr = dict(filter(lambda _,value: not value == (None, None), combined_attributes.items()))
        G.add_nodes_from([(node, combined_attributes[node]) for node in new_nodes])
        G.add_edges_from([(node1, node2, combined_attributes[node1 + "->" + node2]) for (node1,node2) in new_edges])
        
        #sent as a module output and replaces condition.
        return (G, copy.deepcopy(self.constraints)) 

# %% ../nbs/01_lhs_parsing.ipynb 11
def lhs_to_graph(lhs: str, condition):
    """Given an LHS pattern and a condition function, return the directed graph represented by the pattern, 
    along with an updated condition function that combines the original constraints and the new value and type constraints
    deriving from the pattern.

    Args:
        lhs (string): A string in lhs format 
        condition (lambda: Match -> bool): A function supplied by the user specifying additional 
                                           constraints on the graph components.

    Returns:
        DiGraph, lambda: Match->bool: a networkx graph that is the graph represented by the pattern, 
                                      and an extended condition function as mentioned above.
    """
    try:
        tree = lhs_parser.parse(lhs)
        final_graph, constraints = graphRewriteTransformer(component="LHS").transform(tree)
        # constraints is a dictionary: vertex/edge -> {attr_name: (value, type), ...}

        # add the final constraints to the "condition" function
        def type_condition(match: Match):
            flag = True
            for graph_obj in constraints.keys():
                obj_constraints = constraints[graph_obj]
                for attr_name in obj_constraints.keys():
                    required_type, required_value = obj_constraints[attr_name]

                    # check value constraint
                    if required_value != None:
                        if not hasattr(required_value, '__eq__') or (not required_value == match[graph_obj][attr_name]):
                            flag = False
                    
                    # check type constraint only of value was not checked
                    elif required_type != None and not isinstance(match[graph_obj][attr_name], required_type):
                        flag = False

            # True <=> the match satisfies all the constraints.
            return flag and condition(match) 
                
        return final_graph, type_condition
    except (BaseException, UnexpectedCharacters, UnexpectedToken) as e:
        raise GraphRewriteException('Unable to convert LHS: {}'.format(e))

