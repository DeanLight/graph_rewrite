
## Abilities

Match types
* Constant match rewrite
* Recursive matches (tree or graph)
* OR between match substructure 
* Work on full graph as well
* recursive matches on a MACRO pattern
* Enable different traversal orders on the graph

Transform types
* change attributes in nodes
* change attributes in edges
* Delete, mutate, create of nodes/edges/attributes

Constraints
* multiple constraints on matches (also node types?)

python code interactions
* Change node attributes with python expressions/lamda functions
* Add match constraints with lambda functions
* use logical variables of match, as input to transform expressions
  * even inline
* enable adding code python as intermediate state as
  * pre proccessing before transform
  * post proccessing etc..
* Work on multiple graphs
  * Define a match on one graph and then a write on another graph
* Enable controlling the matching lifecycle by the user
  * Hopefully not with custom blocks
  * more like hooks

Metaprogramming
* Templates/Macros for DRY and generlity
  * Bind logical varaible to template
  * Add conditions on top of a template from the outside
* Define a transformation on a template/macro
* Add comments syntax
* Re use of macros across different use cases


## Concepts

* Span rewriting/ double sesqi pushout
  * LHS
  * Projection
  * RHS

* Match (of a subgraph)
* Transform (of a match)
* ~Logical Variable (and possible assignment)
* Graph traversal orders
* Attribute graph

## Constraints
* Within python runtime
  * add intermediate semantic layer that defines the hook points
* To separate the graph engine layer from the conceptual layer
  * So we can switch out graph backends
* Be able to communicate with current algorithms in graph rewriting
  * better matching algorithms
  * Compiling rewriting more efficiently (like regraph)

## Use Case stratification/ desired layers

User types:
* Regular python programmers playing with graphs
* Compiler writers
* Graph transformation gurus

Rule types:
* transforms where you dont change sub graph structure
* Transforms where P/RHS are can be infered automatically
* Constant transforms 
* matches with complex constraints
* Recursive matches
* Macros and templates
* Recursive on complex structures
* Multiple graph interactions
* People who want imperative transforms


## Design

### constant transforms no attribute change

LHS = dot_file with anonymous nodes
RHS = dot_file with anonymous nodes
LHS_pattern ="""
    a->b[x = Value ]->_
"""
RHS_pattern ="""
    a->c
"""

### No structural change to graph

def newNode(..):-> dict
    pass

LHS= """
    a->b[x=3]
"""
transform1={
    "a"= newNode(dsadas),
    "b.x" = 5,
    "a->b" ={
        edge_type = "hello",
        edge_weight = 3
    }
}

transform2={
    "a"= newNode(dsadas),
    "b" = register_and_insert()
    
}

### Big LFS small change

LHS_pattern = """
    a[token: Node, label: Exp, val: Node]
        ->b1[token: ExpNode, label: Exp, var: str, code: str]
        ->op[token: Node, label: AND]
        ->b2[token: ExpNode, label: Exp, var: str, code: str]
"""
RHS_pattern ="""
    <ONLY CHANGES>
    a[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(BOOL_T)]
"""
graph_transform(g,LHS,RHS,delta_rhs=True)


### just match for sideeffect explicitly

LHS= """
    a->b[x=3]
"""
for match in graph_transform(LHS):
    side_effect(engine,match)

or

graph_transform(LHS,side_effect=lambda ....)

### imperative side effect

LHS='''a->b->c'''
def add_to_register_buffer(a,b,c):
    side_effect1
    side_effect2
    new_graph = ...
    return new_graph



```python
LHS = """
"""
P = """
"""
RHS="""
"""

""""""= """

regular_var = python_func()

dot format
with attributes
with macros
with -*->
RELATION(a=a) 
a->b[x=A|B|f(x.y),...]
a[x:Int= f(...)]
def f(logical variable):
    pass

DEFINE MACRO RELATION(a,b,c):
    a->b->c(...)
"""
```

def Relation(x,y):
    return f""" a->B->c[{x=y}]
    """

LHS = f"""
    {Relation(3,5)}
"""

Look up Jinja2