
## Abilities

Match types
- [x] Constant match rewrite
- [] Recursive matches (tree or graph)
- [] OR between match substructure 
- [] Work on full graph as well
- [] recursive matches on a MACRO pattern
- [] Enable different traversal orders on the graph

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
- [x] transforms where you dont change sub graph structure
- [] Transforms where P/RHS are can be infered automatically
- [x] Constant transforms
- [x] matches with complex constraints
- [] Recursive matches
- [x] Macros and templates
* Recursive on complex structures
* Multiple graph interactions
* People who want imperative transforms

## extras: !!!!!
- rewrite(""" """)
- naming edges is not supported, but necessary in changing one edge based on another. Currently, this is performed in 2 different rewritings.
- allow multiple edges between vertices - this requires handeling ambiguity, maybe by naming the edges.
- Match pattern based on negation conditions (doesn't have children / not connected to vertex b...) - i.e. graph sorting

## Design
### general
- blocks (% %) of our syntax, inside real python code. Imported function that links parameters (connect(LHS = ..., )).
- definitions inside our block (LHS = ...) have the same lifespanas the variablesin the function that contains the block.
- "P" is overriden by the <CHANGES ONLY> option. Connected 

### constant transforms no attribute change (only structure)
- the override flag (transformer/visitor) are specified as part of the rewriting command, so a structure can be used as both LHS or RHS later.
- '_' for anonymous node. 
- no need to specify the parent to which the RHS is connected, unless the connection is not trivial (ambiguous).

%%
  L:
    a -> b -> _

  R:
    a -> c 
%%

rewrite(L, R, type=transformer) ### imported

### No structural change to graph
%%
  L:
    <!-- Option A: include attributes in graph structure - syntactic suger -->
    a -> b[value: str = "hello" , id: int] -> c -[weight]-> d -> e
    <!-- Option B: seperate structure and attributes - simplified -->
    a -> b -> c -> d -> e

    b = {
      value: str = "hello"
      id: int
    }

    b->c = {
      weight
    }

  R:
    ~a <!--delete vertex (including attributes). if there are connections, RAISES AN ERROR-->
    ~(b->c) <!--delete edge (including implicit attributes)-->
    ~a.attribute <!--delete a node's attribute-->
    ~(b->c).attribute <!--delete an edge's attribute-->
    <!-- or: b\-[~ attribute]\->c -->

    b -[]-> c  <!--edge attribute--
    b[] -> c #vertice attribute
%%
<!-- transform1={
    "a"= newNode(dsadas),
    "b.x" = 5,
    "a->b" ={
        edge_type = "hello",
        edge_weight = 3
    }
} } -->

### Complex constraints
- '|' stands for "such that", can be written in the syntactic sugar/simplified version of attributes, as follows.
- complex conditions can be f or explicit, as long as it is boolean.
%%
    L:
      <!-- Option A: include attributes in graph structure -->
      a -> b[value: str | f(str) and g(str) , id: int] -> c -[weight | weight > 30]-> d -> e
      <!-- Option B: seperate structure and attributes -->
      a -> b -> c -> d -> e

      b = {
        value: str | f(str)
        id: int
      }

      b->c = {
        weight | weight > 30
      }
%%

### Recursive matches
- '->+' - duplications (one or more) similar to regex.

%%
  LHS:
    _ -> b ->+ c -> _ <!-- one or more instances of the entire specified sub-graph -->
    _ -> d

    LIST(l = d) or (l->item)
  
  LIST:  <!-- recursive pattern definition-->
    l -> item
    l -> d

    LIST(l = d)
%%

### Macros and templates
- macros == regular patterns as used before, can be inforced on vertices.

%%
  PATTERN:
    _ -> b -> c -> d

    PATTERN1(a=d)
  

%%

### Big LHS small change

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