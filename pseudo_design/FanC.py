# MAIN IDEAS:
# token = type of object
# label = name of derivation rule / token
# val = object itself / lexema ($$)
# Allow label = EPSILON for epsilon derivation
# In case of deleting nodes with allocated memory, allow freeing?

## 1) Remove Tokens: 
##      Remove unnececarry tokens, like RGXLOG. Applies for literals (strings, numbers, booleans), as well as
##      for types, ret types and type annotations.
# Exp -> NUM
LHS_pattern = """
	a[token: Node, label: Exp, val: Node]
        ->b[token: String, label: NUM, val: str]
"""
RHS_pattern = """
    new_var = freshVar()

    c[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(INT_T, new_var),
        var: str = new_var, code: str = var + ":=" + b.val]
"""

# Type -> INT
LHS_pattern = """
	a[token: Node, label: Type, val: Node]
        ->b[token: Node, label: INT]
"""
RHS_pattern = """
    c[token: TypeNode, label: Type, val: TypeNode = new TypeNode(INT_T)]
"""

# Exp -> TRUE
LHS_pattern = """
    a[token: Node, label: Exp, val: Node]
        ->b[token: Node, label: TRUE]
"""

RHS_pattern = """
    c[token: Exp, label: Exp, val: new ExpNode("BOOL_T"),
        true
"""

# TypeAnnotation -> /*epsilon*/
LHS_pattern = """
    a[token: TypeAnnotation, label: TypeAnnotation, val: Node]
        ->b[token: Node, label: EPSILON]
"""
RHS_pattern = """
    c[token: TypeAnnotation, label: TypeAnnotation, val: TypeAnnotation = new TypeAnnotation(false)]
"""

## 2) CalcBinaryUnary: 
##      calculate value of numerical expressions (such as 3 + 3).
##      Question: in case of 3 + 3 + 3 + ... + 3, does the micropass run until there are nodes
##      fitting occurences of the LHS? (In that case, such cases are handled well)
##      OR the occurences are saved beforehand and therefore, we have to run this micro pass
##      again and again until there are no such LHS's.
# Exp -> Exp ADDITIVE Exp
LHS_pattern = """
    a[token: Node, label: Exp, val: Node]
        ->num1[token: ExpNode, label: Exp, var: str, code: str]
        ->op[token: String, label: ADDITIVE, val: str]
        ->num2[token: ExpNode, label: Exp, var: str, code: str]
"""

RHS_pattern = """
    new_var = freshVar()
    new_code = num1.code || num2.code || new_var || ":=" || num1.var || op.val || num2.var

    b[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(INT_T, new_var),
        var: str = new_var, code: str = new_code]
"""

## 3) CreateBoolNodes:
##      Create (only) nodes for bool expressions, WITHOUT labels, code, etc. (handled later)
# Exp -> Exp AND Exp
LHS_pattern = """
    a[token: Node, label: Exp, val: Node]
        ->b1[token: ExpNode, label: Exp, var: str, code: str]
        ->op[token: Node, label: AND]
        ->b2[token: ExpNode, label: Exp, var: str, code: str]
"""

RHS_pattern = """
    b[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(BOOL_T)]
        ->b1[token: ExpNode, label: Exp, var: str, code: str]
        ->op[token: Node, label: AND]
        ->b2[token: ExpNode, label: Exp, var: str, code: str]
"""

## 4) Convert
# Exp -> LPAREN Type RPAREN Exp
LHS_pattern = """
    a[token: Node, label: Exp, val: Node]
        ->lparen[token: Node, label: LPAREN]
        ->type[token: Type, label: TypeNode, val: TypeNode]
        ->rparen[token: Node, label: RPAREN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode, code: str, var: str]
"""

RHS_pattern = """
    new_var = freshVar()
    conversion_code = ...

    b[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(type.type, new_var),
        var: str = new_var, code: str = exp.code || conversion_code]
"""

# Exp -> LPAREN Exp RPAREN
LHS_pattern = """
    a[token: Node, label: Exp, val: Node]
        ->lparen[token: Node, label: LPAREN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode, code: str, var: str]
        ->rparen[token: Node, label: RPAREN]
"""

RHS_pattern = """
    exp
"""

## 5) Expression list
##      for lists of expressions.
##      QUESTION: if expNodes are pointers (expNode*), then this pass is fine.
##      otherwise (copies) then we need to move it to a later time, since not all expressions have their
##      vars and codes calculated by this time (such as short circuit evaluated booleans).
# ExpList -> Exp COMMA ExpList
LHS_pattern = """
    a[token: Node, label: Exp, val: Node]
        ->exp[token: ExpNode, label: Exp, val: ExpNode, code: str, var: str]
        ->comma[token: Node, label: COMMA]
        ->list[token: ExpListNode, label: ExpList, val: ExpListNode]
"""

RHS_pattern = """
    new_list[token: ExpListNode, label: ExpList, val: ExpListNode = list.append(exp)]
"""

## 6) StatementsSetUp
##      Build only nodes for statements, without code and "next" labels.
# Statement -> ID ASSIGN Exp SC
LHS_pattern = """
    a[token: Node, label: Statement, val: Node]
        ->id[token: String, label: ID, val: String]
        ->assign[token: Node, label: ASSIGN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode, code: str, var: str]
        ->sc[token: Node, label: SC]
"""

RHS_pattern = """
    b[token: Statement, label: Statement]
        ->id[token: String, label: ID, val: String]
        ->assign[token: Node, label: ASSIGN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode, code: str, var: str]
        ->sc[token: Node, label: SC]
"""

# Statement -> IF LPAREN Exp RPAREN Statement
LHS_pattern = """
    a[token: Node, label: Statement, val: Node]
        ->if[token: Node, label: IF]
        ->lparen[token: Node, label: LPAREN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode with val.type = BOOL_T, code: str, var: str]
        ->rparen[token: Node, label: RPAREN]
        ->sts[token: Statement, label: Statement, code: str]
"""

RHS_pattern = """
    b[token: Statement, label: Statement]
        ->if[token: Node, label: IF]
        ->lparen[token: Node, label: LPAREN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode with val.type = BOOL_T, code: str, var: str]
        ->rparen[token: Node, label: RPAREN]
        ->sts[token: Statement, label: Statement, code: str]
"""

## 7) InitLables
##      handle calculation of next, trueList, falseList labels, top down.
##      allows calculation of short-ciruit, as well as order of commands.
# Program -> Statement
LHS_pattern = """
    p[token: Node, label: Program]
        ->sts[token: Statement, label: Statement]
"""

RHS_pattern = """
    p[token: Program, label: Program]
        ->sts[token: Statement, label: Statement, next: str = freshLabel()]
"""

# Statement -> Statement; Statement
LHS_pattern = """
    s[token: Statement, label: Statement, next: str]
        ->s1[token: Statement, label: Statement]
        ->semicolon[token: Node, label: SC]
        ->s2[token: Statement, label: Statement]
"""

RHS_pattern = """
    s[token: Statement, label: Statement]
        ->s1[token: Statement, label: Statement, next: str = freshLabel()]
        ->semicolon[token: Node, label: SC]
        ->s2[token: Statement, label: Statement, next: str = s.next]
"""

# Statement -> IF LPAREN Exp RPAREN Statement
LHS_pattern = """
    b[token: Statement, label: Statement, next: str]
        ->if[token: Node, label: IF]
        ->lparen[token: Node, label: LPAREN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode with val.type = BOOL_T, code: str, var: str]
        ->rparen[token: Node, label: RPAREN]
        ->sts[token: Statement, label: Statement, code: str]
"""

RHS_pattern = """
    trueLabel = freshLabel()
    
    c[token: Statement, label: Statement, next: str, code: str = exp.code || trueLabel || ":" || sts.code]
        ->if[token: Node, label: IF]
        ->lparen[token: Node, label: LPAREN]
        ->exp[token: ExpNode, label: Exp, val: ExpNode with val.type = BOOL_T, code: str, var: str,
                trueLabel: str = trueLabel, falseLabel: str = b.next]
        ->rparen[token: Node, label: RPAREN]
        ->sts[token: Statement, label: Statement, code: str, next: str = b.next]
"""

# Exp -> Exp AND Exp
LHS_pattern = """
    b[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(BOOL_T), trueLabel: str, falseLabel: str]
        ->b1[token: ExpNode, label: Exp, var: str, code: str]
        ->op[token: Node, label: AND]
        ->b2[token: ExpNode, label: Exp, var: str, code: str]
"""

RHS_pattern = """
    new_label = freshLabel()

    b[token: ExpNode, label: Exp, val: ExpNode = new ExpNode(BOOL_T), code: str = b1.code || new_label || ":" || b2.code, trueLabel: str, falseLabel: str]
        ->b1[token: ExpNode, label: Exp, var: str, code: str, trueLabel: str = new_label, falseLabel: str = b.falseLabel]
        ->op[token: Node, label: AND]
        ->b2[token: ExpNode, label: Exp, var: str, code: str, trueLabel: str = b.trueLabel, falseLabel: str = b.falseLabel]
"""

## 8) Accumulate code
##      bottom up pass, concatenate the code strings such that eventually, the Program node holds in his "code" attribute
##      the entire code for the program.
# Statement -> Statement SC Statement
RHS_pattern = """
    s[token: Statement, label: Statement]
        ->s1[token: Statement, label: Statement, next: str, code: str]
        ->semicolon[token: Node, label: SC]
        ->s2[token: Statement, label: Statement, next: str, code: str]
"""

LHS_pattern = """
    code = s1.code || next || ":" || s2.code
    
    new_s[token: Statement, label: Statement, code: str = code]
"""

## 9) Run
##      get the code from program (only one occurance) and run it!
# Program -> Statement
RHS_pattern = """
    p[token: Program, label: Program]
        ->sts[token: Statement, label: Statement, next: str, code: str]
"""

LHS_pattern = """
    end_label = freshLabel()
    full_code = sts.code || end_label || ":"
    run(full_code)
"""



