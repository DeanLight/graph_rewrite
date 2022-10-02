## Design
updated: 23.9.2022
### General
- ';' seperates different components of LHS/RHS
- Library functions:
  ```python
  typedef dict[Hashable, dict] as Match # where Node can represent both edge, vertex
  typedef tuple(list[Match],list[Match]) as ResultSet #[0] - vertices, [1] - edges
  class TransTypes(Enum):
    TRANSFORMER = 1
    VISITOR = 2

  def rewrite(lhs: list, p=None, rhs=None, condition=None, apply=None, 
              type=TransTypes.TRANSFORMER) -> ResultSet:
    """
      lhs: a list of strings to allow the logical OR feature (details below).
      p: string, in order to specify vertex duplications.
      rhs: a formatted string to allow future rendering (inside implementation) according to each    match's actual values.
      condition: function: Match -> bool, 
      apply: function: Match -> void
      type: TransTypes object
      return value: result set
    """
    pass
  ```
- ResultSet is a tuple to allow edge-naming, and thus matching (details below).


### Constant transforms no attribute change (only structure)
- the override flag (transformer/visitor) are specified as part of the rewriting command, so a
  structure can be used as both LHS or RHS later.
- '_' for anonymous node. 
- Need to specify the parent to which the RHS is connected, the connection might be not trivial
  (ambiguous).

```python
L = "a -> b -> _"
R = "a -> c"
rewrite(lhs=L, rhs=R, type=TransTypes.TRANSFORMER)
```
### No structural change to graph
- this can be easily implemented using type = "visitor"
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

rewrite(lhs=L, rhs=R, type=TransTypes.TRANSFORMER)
```

### Complex constraints
- '|' stands for "such that", can be written in the syntactic sugar/simplified version of
  attributes, as follows.
- complex conditions can be a function or explicit, as long as it is boolean.

```python
def f(x: str):
  ...
  return True # or some boolean
  
rewrite(lhs=L, rhs=R ,condition=(match)->{return f(match["b"].value)}, type=TransTypes.TRANSFORMER)
# de we still need Match()? discussed in side effects
```
### multiple generic connections 
- '-+->' - duplications (one or more) similar to regex. One or more instances of the entire specified sub-graph
  only legal in the LHS (because the RHS should not be ambigous.)
- in the resultSet, 'c' is now multiplied. the result set contains "d<0>"...
- numbering of instances is inforced as part of the matching.
- recursive duplications are allowed, d<0,1,5>...
- inforcing an explicit number of connections is done by: -_num_->

```python
#a-[*]->b in neo4j = all the connections from a to other b's

l = """  _ -> b -+[weight:int]-> c -> d[value:int]
    d<0> -> e
    d<5> -> e
"""
res = rewrite(lhs=l, rhs=None, type=TransTypes.VISITOR)
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

### Macros and templates
- macros == regular patterns as used before, can be enforced on vertices.

- macros with anonymus entities:
```python
pattern1 = f"""{a}-> __[value: int]""" #actually the constraint is inside condition...
L = f"""_ -> e -> c -> d;
    {pattern1.render(a='d')} ; {pattern1.render(a='c')}"""
```

- macros with named entities: only used for shortening of strings for the user.
- in this case the result set will contain numbered strings(?)
```python
pattern1 = f"""{a}-+->e{num}[value: int = 6]"""
l = f"""_ -> e -> c -> d;
    {pattern1.render(a='d',num=1)} ; {pattern1.render(a='c',num=2)}"""

results_set = rewrite(lhs=l, rhs=None, type=TransTypes.VISITOR)
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
R = f'''a[token: ExpNode, label: Exp, val: ExpNode = {x}]'''

rewrite(L,R,apply= f)
#not match-dependent but this usage of 'apply' is also ok to avoid heavy parsing.
def f(match): 
  return new ExpNode(BOOL_T)

rewrite(lhs=L, rhs=R, type=TransTypes.VISITOR)
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
result_set = rewrite(lhs=L, condition=(match)->{return f(match["b"].my_value)}, type=TransTypes.TRANSFORMER)

for match in results_set: #is there a defined order of graph iteration?
  sum += match["b"].my_value
```

### example for 'apply'
```python
def f(match):
  return match["b"].value + match["c"].value

LHS = "a->b[value]; \
    a->c[value]"
RHS = f"""a[value ={x}]"""
rewrite(g, rhs=RHS, lhs=LHS,apply=dict_of_rendering{...}, type=TransType.TRANSFORMER)
```

### choosing one of several LHS
to allow the user to select one of several constraints, LHS is supplied as a list of formatted-strings. the matching algorithm finds graph components that match one or more of the constraints. (logical 'OR')

### naming edges - 10%
- therefore the resultset is a tuple of lists (one for vertices and one for edges).
```python
l = """ a->b->c 
b->c = {
  $var_name = x
}
"""
```
### allowing collapse of structural recursion
- Relevant mainly for parsing purposes. Convert a graph of sequence format to the fully evaluated version of it.
- i.e., a list can be represented by the user as a tree with depth equal to the length of the list.
  the tree can be converted to a 2-layered tree with the elements of the list as direct children of the root.
