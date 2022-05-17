#pseudo code for RGXLOG micropasses

#NOTE: RGXLOG existing implementation replaces "STRING" child to be a string inside a "children" array.
#      we chose to include the string as a structural child of the parent node, as a node with token "CHILD".
#NOTE: where RGXLOG asserts expected graph structure, and uses the children for calculations, we included the internal
#      structure in the LHS.
###########################################################

## Remove Tokens: 
## Traverse the graph using a user-defined order. search for vertices of redundant tokens with sons of real value, 
## create a new tree based on that. (remove  “INT” , put int=6 in the new graph).

# INT
LHS_pattern ="""
    a->b[token: INT, val: str]
"""
RHS_pattern ="""
    a->c[token: CHILD, val: integer = int(b.val)]
"""
    
# STRING
LHS_pattern ="""
    a->b[token: STRING, val: str]
"""
RHS_pattern ="""
    a->c[token: CHILD, val:str = b.val[1:-1]]
"""

# LOWER_CASE_NAME
LHS_pattern ="""
    a->b[token: LOWER_CASE_NAME, val: lark.Token]
"""
RHS_pattern ="""
    a->c[token: CHILD, val:str = b.val.value]
"""

# UPPER_CASE_NAME
LHS_pattern ="""
    a->b[token: UPPER_CASE_NAME, val: lark.Token]
"""
RHS_pattern ="""
    a->c[token: CHILD, val:str = b.val.value]
"""


## Fix Strings: 
## traverse the tree, node and make changes on sons.
## Use lambda from user to replace son’s value based on the previous value.

# string
LHS_pattern ="""
    a[token: string] -> b[token: CHILD, val: str]
"""
RHS_pattern ="""
    a[token: string] -> c[token: CHILD, val: str = b.val.replace('\\\n', '')]
"""

## Check Reserved Relation Names: 
## search nodes by type (“relation”) , if found check the content (the relation name itself). 
## Also use lambda as suggested.

LHS_pattern ="""
    a[token: relation_name] -> b[token: CHILD, val: str]
"""
RHS_pattern ="""
    check(b.val)
    
    def check:
        ...
"""

## Convert Span Nodes To Span Instances:  
## search nodes by type (“span”), replace direct sons with new single vertice holds the value of the removed sons (“(x,y)”).
## change the current graph.

LHS_pattern ="""
    a[token: span] -> b[token: int] -> c[token: CHILD, val: integer]
    a -> d[token: int] -> e[token: CHILD, val: integer]
"""
RHS_pattern ="""
    a[token: span] -> f[token: CHILD, val: Span = Span(c.val, e.val)]
"""
####################### Convert Statements To Structured Nodes: ###################
## assignment - search nodes by type (assignment), 
##              remove direct sons and replace with a single assignment object, constructed based on the former children.

LHS_pattern ="""
    a[token: assignment] -> b[token: var_name_node]             -> c[token: CHILD, val: str]
    a                    -> d[token: value_type_node, val: str] -> e[token: ___ ,val:term]
"""
RHS_pattern ="""
    a->f[token: CHILD, val: Assignment = Assignment(c.val, e.val, d.val)]
"""

## “read” assignment - reading a string from a file. 
## Create the structured node and use it as a replacement for the current assignment representation.
LHS_pattern ="""
    a[token: assignment] -> b[token: var_name_node]             -> c[token: CHILD, val: str]
    a                    -> d[token: read_arg_node, val: str]   -> e[token: ___ ,val:term]
"""
RHS_pattern ="""
    a -> f[token: CHILD, val: Assignment = ReadAssignment(c.val, e.val, d.val)]
"""

## add fact
## add a child of the current ‘fact’ node, constructed based on the current parent node (converted into ‘relation’ node).
LHS_pattern ="""
    a
    RELATION(a=a) 
    
    RELATION:
    a[token: relation] -> b[token:relation_name, ] -> c[token: CHILD, val: str]
    a -> d[token: term_list_node] +-> e[token:term_node, val:srt] -> f[token: ___ ,val:term]
""" #optional syntax +->. 
RHS_pattern ="""
    relation = f(a) """#what should we pass to f? we need an explicit match to a macro.
    """
    r = AddFact(relation.relation_name, relation.term_list, relation.type_list)
    a -> b[val:AddFact = r)]
    
    def f(RELATION):
        relation_name = c.val
        term_list = [f.val] """ #optional syntax: f[i].val gives the f vertice of the i'th copy, from left to right.
        """
        type_list = [DataTypes.from_string(e.val)]
        return Relation(relation_name, term_list, type_list)
"""

## remove fact - same, but different replacement node.
LHS_pattern ="""
    a
    RELATION(a=a) 
""" 
RHS_pattern ="""
    relation = f(a)
    r = RemoveFact(relation.relation_name, relation.term_list, relation.type_list)
    a -> b[val:RemoveFact = r]
"""

## query
LHS_pattern ="""
    a
    RELATION(a=a) 
""" 
RHS_pattern ="""
    relation = f(a)
    q = Query(relation.relation_name, relation.term_list, relation.type_list)
    a -> b[val:AddFact = q]
"""

## relation declaration - create a list of types based on children, 
##                        replace all children with a single node containing the list (special object).
LHS_pattern ="""
    a
    DECL(a=a)
    
    DECL:
    a[token: relation_decl_node] -> b[token:relation_name] -> c[token: CHILD, val: str]
    a -> d[token: decl_term_list_node] +-> e[token:decl_term_node, val: str]
"""
RHS_pattern ="""
   a -> [val:RelationDeclaration, val: g()]

   def g(DECL):
    type_list = []
    for decl_term_type in [e.val]:
        if decl_term_type == "decl_string":
            type_list.append(DataTypes.string)
        elif ...

    return RelationDeclaration(relation_name, type_list)    
"""



## rule - same replacement of children.

LHS_pattern ="""
    a[token: rule_node] -> rule_head[token: rule_head_node]
    a -> f[token: rule_body_relation_nodes] +-> g[val: str] """ #g also has a value,and is a relation node as described below.
    """
    RELATION(a=rule_head)
    IE_RELATION(a=g) or RELATION(a=g)"""# each f is a relation or an IE relation
    #this is another MACRO. RELATION is already defined above but appears here for convinience.
    """
    RELATION:
    a[token: relation] -> b[token:relation_name, ] -> c[token: CHILD, val: str]
    a -> d[token: term_list_node] +-> e[token:term_node, val:srt] -> f[token: ___ ,val:term]
    
    IE_RELATION:
    a -> b[token:relation_name, ] -> c[token: CHILD, val: str]
    a -> d +-> e[token:term_node, val:srt] -> f[token: ___ ,val:term]
    a -> g +-> h[token:term_node, val:srt] -> i[token: ___ ,val:term]
"""
    
RHS_pattern ="""
   a -> [val:Rule, val: g()]
   """
   # functions that operate on the direct RHS pattern do not recieve any parameters.
   """
   def g():
        structured_body_relation_list = []

        for g:
            decl_term_type = g.val
            if decl_term_type == "decl_string":
                x = f()
            elif (...)
                x = f_ie()
            structured_body_relation_list.append(x)
            
        structured_head_relation_node = f(rule_head)
        body_relation_type_list = [g.val]
        return Rule(structured_head_relation_node, structured_body_relation_list, body_relation_type_list)  
    
    def f_ie(IE_RELATION):
        output_term_list_node = ie_relation_node.children[2]

        relation_name = c.val

        input_term_list = [f.val]
        input_type_list = [DataTypes.from_string(e.data)]

        output_term_list = [i.val]
        output_type_list = [DataTypes.from_string(h.val)]

        return IERelation(relation_name, input_term_list, input_type_list, output_term_list, output_type_list)
"""