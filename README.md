# Graph Rewrite

## Description
Graph Rewrite is a python library for performing graph transformations using a declerative approach. 

### Motivation
The original motivation for our project derives from the domain of compiler development. During compilation, large internal graphs such as AST's are constructed, and later modified (these graph modifications in context of compilers are called 'passes'), thereby creating the need for a convinient tool to handle such graph transformations. 
Thus, our goal in developing the Graph Rewrite library is to allow a more intuitive handling of large patterns with more complex side effects (by using a declerative approach). 

## Installation
To download and install Graph Rewrite, run the following commands in your terminal:
```bash
# Install package given a conda environment with python>3.9
git clone https://github.com/DeanLight/graph_rewrite
cd graph_rewrite
pip install -e .

```
## Usage
The user interface includes a single function called _rewrite_, by which graph transformations are made.
The user provides specifications for 3 NetworkX graphs: *LHS*, *P* and *RHS* (as elaborated [here](https://github.com/DeanLight/graph_rewrite/blob/a72e6e37a13c1ab8dbc72c7d9169a13e78dcd31f/nbs/05_rules.ipynb#L27)), which together with some additional parameters define the requested subgraphs to be found in the input graph and the transformation to be performed.

Examples:
- Find all vertices with two successors and remove the edges:
```python
# input_graph is a networkX directed graph.
matches = rewrite(input_graph,
        lhs='a->b; a->c', p='a;b;c', is_recursive=True)
```

- find all the pairs of parent-successor in which the parent has the 'val' attribute, increase it's value by 1, and place the result in the connecting egde. 
```python
matches = rewrite(input_graph,
        lhs='a[val]->b', p='a->b', rhs='a-[val={{new_val}}]->b', 
        render_rhs={'new_val': lambda match: match['a']['val'] + 1}, is_recursive=False)
```

We welcome you to view further [examples and use cases](https://github.com/DeanLight/graph_rewrite/blob/b637c480dfa1e8d9710ab4bcdf884d1b3e023d01/nbs/06_transform.ipynb#L850), as well as the documentetion of _rewrite_.
An elaborated specification of the 3 networkX patterns suppplied by the user can be found [in the _rules_ module](https://github.com/DeanLight/graph_rewrite/blob/a72e6e37a13c1ab8dbc72c7d9169a13e78dcd31f/nbs/05_rules.ipynb#L596)
## Resources
- [ReGraph](https://github.com/Kappa-Dev/ReGraph) library (allows graph transformations using an imperative interface)

- Following the motivation section above, as a part of our integration tests we implemented the internal-graph transformations (also called "passes") of the [SpannerWorkbench](https://github.com/DeanLight/spanner_workbench) interpreter.

- [lark library documentation](https://lark-parser.readthedocs.io/en/latest/json_tutorial.html) - used in our mudules and in the Spanner Workbench passes we implement.
