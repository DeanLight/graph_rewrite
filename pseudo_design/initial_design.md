
## Abilities

Match types
- [] Constant match rewrite
<!-- - [] Recursive matches (tree or graph) -->
- [] OR between match substructure 
- [] Work on full graph as well
<!-- - [] recursive matches on a MACRO pattern -->
- [] Enable different traversal orders on the graph

Transform types
- [] change attributes in nodes
- [] change attributes in edges
- [] Delete, mutate, create of nodes/edges/attributes

Constraints
- [] multiple constraints on matches (also node types?)

python code interactions
- [] Change node attributes with python expressions/lamda functions
- [] Add match constraints with lambda functions
- [] use logical variables of match, as input to transform expressions
  * even inline
- [] enable adding code python as intermediate state as
  * pre proccessing before transform
  * post proccessing etc..
- [] Work on multiple graphs
  * Define a match on one graph and then a write on another graph
- [] Enable controlling the matching lifecycle by the user
  * Hopefully not with custom blocks
  * more like hooks

Metaprogramming
- [] Templates/Macros for DRY and generlity
  * Bind logical varaible to template
  * Add conditions on top of a template from the outside
- [] Define a transformation on a template/macro
- [] Add comments syntax
- [] Re use of macros across different use cases


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
- [x] multiple generic connections 
- [x] Macros and templates
<!-- - [] Recursive on complex structures (depth unpacking) -->
- [x] naming edges - supported in 10%. (necessary in changing one edge based on another).
<!-- - [] Multiple graph iteration -->
- [] People who want imperative transforms

## extras if time allows:
- rewrite(""" """)
- allow multiple edges between vertices - this requires handeling ambiguity, maybe by naming the
  edges.
- Match pattern based on negation conditions (doesn't have children / not connected to vertex b...).
  implement by ^$
- i.e. graph sorting

## Design
### general
- blocks (% %) of our syntax, inside real python code. Imported function that links parameters (connect(LHS = ..., )).
- definitions inside our block (LHS = ...) have the same lifespanas the variablesin the function that contains the block.
- "P" is overriden by the <CHANGES ONLY> option. Connected 
- ';' seperates different components of LHS/RHS

- Library functions:
  ```python
  typedef dict[str, Node] as Match # where Node can represent both edge, vertex
  typedef tuple(list[Match],list[Match]) as ResultSet #[0] - vertices, [1] - edges
  rewrite(target: graph/match, lhs: str, p: str = None, rhs: str = None, condition: ((Match, ...) -> bool) = None, apply=((Match, ...)-> void) = None  type: str = "transformer" ) -> ResultSet
  ```

### constant transforms no attribute change (only structure)
- the override flag (transformer/visitor) are specified as part of the rewriting command, so a
  structure can be used as both LHS or RHS later.
- '_' for anonymous node. 
- Need to specify the parent to which the RHS is connected, the connection moght be not trivia
  (ambiguous).

```python
L = "a -> b -> _"
R = "a -> c"
rewrite(lhs=L, rhs=R, type="transformer")
```
### No structural change to graph
- this can be easily implemented using typr = "visitor"
- transformer - replaces the LHS with the RHS.
```python
L = "a -> b -> c -[weight: int]-> d -> e; \
     c -> d; \
      \
     b = { \
       value: str = \"hello\", \
       id: int \
     }"
P = "b -> b1; b -> b2"
R = "a -> b[value: str = \"hello 2\"] -> c -[weight: int]-> d -> e; \
     c -> d; \
     b = { id: int }"

rewrite(lhs=L, rhs=R, type="transformer")
```

### Complex constraints
- '|' stands for "such that", can be written in the syntactic sugar/simplified version of
  attributes, as follows.
- complex conditions can be f or explicit, as long as it is boolean.

```python
def f(x: str):
  ...
  return True # or some boolean

#example 1

str = "something"
L = f"""a -> b[value = {str} | {f(str)}] -> c -> d -> e;

    b = {
      id: int
    };

    b->c = {
      weight | weight > 30
    }"""

#example 2 - explicit conditions that are not defined outside by the user, may ba parsed without formatting.

L = f"""a -> b[value: str | value > 30] -> c -> d -> e;

      b = {
        id: int
      }
      """
      
#example 3

L = f"""a -> b[value: str] -> c -> d -> e;

      b = {
        id: int
      };

      b->c = {
        weight | weight > 30
      }"""

#option 2
# condition is always f:match --> bool
rewrite(lhs=L, rhs=R ,condition=(match)->{return f(match["b"].value)}, type=transformer)
# de we still need Match()? discussed in side effects
```
### multiple generic connections 
- '-+->' - duplications (one or more) similar to regex. One or more instances of the entire specified sub-graph
- tn the resultSet, 'c' is now multiplied. the result set contains "d<0>"...
- numbering of instances is inforced as part of the matching.
- recursive duplications are allowed, d<0,1,5>...
- inforcing an explicit number of connections is done by: -_num_->

```python
#a-[*]->b in neo4j = all the connections from a to other b's

l = """  _ -> b -+[weight:int]-> c -> d[value:int]
    d<0> -> e
    d<5> -> e
"""
res = rewrite(lhs=l, rhs=None, type="visitor")
for match in results_set: #is there a defined order of graph iteration?
  sum += match["d<0>"].value

#another example
l1 = """  _ -> b -+-> d[value:int]
    d<0> -7-> e
    e<0,5> -> _
"""

l2 = """  _ -> b -+-> d[value:int]
    d<0> -7-> e
    e<0,5> -> _
"""
```

<!--### Recursive matches - MAYBE -->
  <!-- LHS =
    _ -> b ->+ c -> _ <!-- one or more instances of the entire specified sub-graph 
    _ -> d

    LIST(l = d) or (l->item)
  
  LIST:   recursive pattern definition
    l -> item
    l -> d

    LIST(l = d) -->
### Macros and templates
- macros == regular patterns as used before, can be enforced on vertices.

- macros with anonymus entities:
```python
pattern1 = f"""{a}->_[value: int = 6]"""
L = f"""_ -> e -> c -> d;
    {pattern1.render(a='d')} ; {pattern1.render(a='c')}"""
```

- macros with named entities: only used for shortening of strings for the user.
- in this case the result set will contain numbered
```python
pattern1 = f"""{a}-+->e{num}[value: int = 6]"""
l = f"""_ -> e -> c -> d;
    {pattern1.render(a='d',num=1)} ; {pattern1.render(a='c',num=2)}"""

res = rewrite(lhs=l, rhs=None, type="visitor")
for match in results_set: #is there a defined order of graph iteration?
  sum += match["e2<3>"].value
```
- this is necessary to prevent bad translation such as:
<!-- 
L = _ -> e -> c -> d; 
    d -> e[...];
    c -> e[...] -->
- macros can be inforced twice in the same vertex, with different numbering.

### visiting - intead of replacing the entire LHS
- demonstration of using type = "visitor"
```python
L = "a[token: Node, label: Exp, val: Node] \
        ->b1[token: ExpNode, label: Exp, var: str, code: str] \
        ->op[token: Node, label: AND] \
        ->b2[token: ExpNode, label: Exp, var: str, code: str]"
R = "a[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(BOOL_T)]"

rewrite(lhs=L, rhs=R, type="visitor")
```
### imperative side effect
- result_set is a **read-only** list of dicts, representing the found matches **before** the changes caused by RHS (if any occured).
- allows modifications of local parameters and retrieving direct values, which is not possible
  inside a function.
- condition allows filtering matches.
- rhs is not mandatory!

```python
# Example: for every matched a->b[my_value: int] in graph, if my_value > 5, add my_value to local variable "sum". Graph won't be changed because rhs is None by default!
sum = 0
def f(num: int):
  return num > 5

L = "a->b[my_value: int]"
result_set = rewrite(lhs=L, condition=(match)->{return f(match["b"].my_value)}, type=transformer)

for match in results_set: #is there a defined order of graph iteration?
  sum += match["b"].my_value
```
### naming edges
- belongs to 10%

```python
l = """ a->b->c 
b->c = {
  $var_name = x
}
"""
```
### some other dilemas
there will be a defined syntax for capture groups in graph_rewrite strings. we can't use \k... like in regex because this is not an ordinary regex template - the lexema's are vertices.

## case 1 - simplest use
```python
LHS = "a->b->c"
RHS = "a[token: b.attr]->c"
rewrite(LHS, RHS, flag=Transform)
```

## case 2 - parsing of actions, without using formatting (f"...")
```python
LHS = "a->b[value]; \
      a->c[value]"
RHS = "a[value = b.value + c.value]"
rewrite(LHS, RHS, flag=Transform)
```
## case 3 - using formatting to avoid extra parsing, but with overhead for the user of defining a function for every simple action. 
```python
LHS = "a->b[value]; \
      a->c[value]"
#dict = match(LHS) # like in regex capture group
results = rewrite(g, lhs=LHS)
for match in results:
  RHS = f"a[value: {f(match["b"].value, match["c"].value)}]"
  rewrite(match, rhs=RHS, flag=Transform)


def f(x,y):
  return x+y


### example for 'apply'
def f(match):
  return match["b"].value + match["c"].value

LHS = "a->b[value]; \
    a->c[value]"
RHS = f"""a[value ={x}]"""
rewrite(g, rhs=RHS, lhs=LHS,apply=dict_of_rendering{...}, flag=Transform)

```
## tradeoff - parsing complex operations inside the LHS, or returning a representive python object that has the same attribute as the vertex, the object is returned in a dict (case 3). 

# OR
```python
L = "a->b->c;\
    {M(a)} OR {X(a)} OR {N(a)}"

L = "a->b->c;\
    a->d OR a->e->f OR a->x"
```
