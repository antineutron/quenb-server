#!/usr/bin/env python
from pyparsing import Optional, Word, Combine, Literal, CaselessLiteral, Forward, CaselessKeyword
from pyparsing import alphas, nums, alphanums, QuotedString, infixNotation, opAssoc
from pyparsing import ParseException, ZeroOrMore

### AST Classes ###

# Several "borrowed" and modified from the SimpleBool example
# The evaluate() function takes a dictionary of variable name => value
# pairs for evaluation at runtime. These will be "facts" about
# the QuenB client e.g. mac address, IP, client ID

# Binary operators (and/or)
class BoolBinOp(object):
    def __init__(self,t):
        self.args = t[0][0::2]
    def __str__(self):
        sep = " %s " % self.reprsymbol
        return "BinOp(" + sep.join(map(str,self.args)) + ")"
    def evaluate(self, vardict):
        return self.evalop(a.evaluate(vardict) for a in self.args)
    __repr__ = __str__

class BoolAnd(BoolBinOp):
    reprsymbol = '&'
    evalop = all

class BoolOr(BoolBinOp):
    reprsymbol = '|'
    evalop = any

# Unary "not" operator
class BoolNot(object):
    def __init__(self,t):
        self.arg = t[0][1]
    def evaluate(self, vardict):
        return not self.arg.evaluate(vardict)
    def __str__(self):
        return "NOT(" + str(self.arg) + ")"
    __repr__ = __str__


# A constant value such as a string or int
class Constant:
    def __init__(self, t):
        #from pprint import pformat
        #print "new Constant: "+pformat(t)
        self.value = t[0]
    def __str__(self):
        return "Const:<"+str(self.value)+">"
    def evaluate(self, vardict):
        return self.value

# A variable ("fact" about a client)
class Variable:
    def __init__(self, t):
        self.name = t[0]
    def __str__(self):
        return "Var:<"+str(self.name)+">"
    def evaluate(self, vardict):
        # If the variable is unbound, return false; we can't match self rule segment
        if self.name in vardict:
            return vardict[self.name]
        else:
            return False

# A comparison operator such as ==
class Comparator:
    # See SimpleCalc example from PyParsing
    opn = {
        "=="  : ( lambda a,b: a == b ),
        "!="  : ( lambda a,b: a != b ),
        ">"   : ( lambda a,b: a > b  ),
        ">="  : ( lambda a,b: a >= b ),
        "<"   : ( lambda a,b: a < b  ),
        "<="  : ( lambda a,b: a <= b ),
    }
    def __init__(self, t):
        self.op = t[0]
        self.func = self.opn[self.op]
    def __str__(self):
        return "CompOp<"+self.op+">"

# A full boolean expression with comparisons, constants,
# variables, brackets and boolean operators
class ComparisonExpression:

    def __init__(self,t):
        self.lhs      = t[0]
        self.operator = t[1]
        self.rhs      = t[2]
    def __str__(self):
        return "CompExp:<"+str(self.lhs)+" "+str(self.operator)+" "+str(self.rhs)+">"

    def evaluate(self, vardict):
        
        return self.operator.func(self.lhs.evaluate(vardict), self.rhs.evaluate(vardict))
        
    __repr__ = __str__

class QuenbRuleParser:
    """
    A rule-parsing class (using PyParsing): parses QuenB rules, which are boolean expressions.
    """

    ### Tokens (lexer-ish) ###
    
    # Just a number 0-9+
    number = Word(nums)
    
    # +/- symbol for numbers
    plusminus = Literal('+') | Literal('-')
    
    # Integer, positive or negative
    const_integer = Combine(Optional(plusminus) + number)
    #const_integer.setParseAction(lambda tokens: int(tokens[0]))
    
    # Floating point number, positive or negative
    const_float = Combine(Optional(plusminus) + Optional(number) + '.' + number)
    #const_float.setParseAction(lambda tokens: float(tokens[0]))
    
    # String, single or double quoted
    const_string = QuotedString('"', escChar='\\', unquoteResults=True) | QuotedString("'", escChar='\\', unquoteResults=True)
    #const_string.setParseAction(lambda tokens: str(tokens[0]))
    
    # Boolean values
    # NB set the parse action here as booleans are "more special" than other constants,
    # as they can be an entire expression on their own
    const_bool  = CaselessKeyword( "true" ) | CaselessKeyword( "false" ).setParseAction(Constant)
    #const_bool.setParseAction(lambda tokens: Constant(tokens[0].lower() == 'true'))
    
    # Any constant
    constant = Combine(const_bool | const_float | const_integer | const_string).setParseAction(Constant)
    
    
    # Variable names (alphanumerics and underscores, start with a letter)
    variable = Word( alphas, alphanums + '_' ).setParseAction(Variable)
    
    # Comparables (constants and variables)
    comparable = constant | variable
    
    # Parentheses for grouping
    lpar  = Literal( "(" ).suppress()
    rpar  = Literal( ")" ).suppress()
    
    # Boolean operators, python-style
    op_and = CaselessLiteral( "and" )
    op_or  = CaselessLiteral( "or" )
    op_not = CaselessLiteral( "not" )
    
    
    # Comparison operators, C/python-style
    op_comparison = (
      Literal( "==" ) | Literal( "!=" ) | Literal( ">=" ) | Literal( "<=" ) | Literal( ">" ) | Literal( "<" )
    ).setParseAction(Comparator)
    
    
    
    ### Compound expressions (parser-ish) ###
    
    # Comparison expressions and booleans (comparison or true/false)
    
    # Comparison - e.g. 'foo == "shoes"'
    exp_comparison = Forward()
    exp_comparison << (
      comparable + op_comparison + comparable
    ).setParseAction(ComparisonExpression)
    
    # Boolean expressions, without operators
    exp_boolean = Forward()
    exp_boolean << (
    
      # ( expression in parens )
      lpar + exp_boolean + rpar |
    
      # foo == 'shoes'
      exp_comparison |
    
      # false
      const_bool
    )
    
    
    # Boolean expressions with operator precedence
    expression = exp_boolean | infixNotation( exp_boolean,
        [
            (op_not, 1, opAssoc.RIGHT, BoolNot),
            (op_and, 2, opAssoc.LEFT,  BoolAnd),
            (op_or,  2, opAssoc.LEFT,  BoolOr),
        ]
    )
 
    def evaluateRule(self, rule, variables):
        
        # Seems obvious... no rule text, evaluate to false
        if rule == None:
            return false

        rule = rule.strip()
        # Fudge factor 0.5 - really need TODO fix parser to generate AST node for true/false...
        if (rule.lower() == 'true' or rule.lower() == 'false'):
            return bool(rule)

        return self.expression.parseString(rule)[0].evaluate(variables)
    
    
    def test(self):
        """
        Not much of a test suite really, I'm sure somebody will care. Someday...
        """
        tests = (
          ("int", self.comparable, "12"),
          ("negative int", self.comparable, "-12"),
          ("positive int", self.comparable, "+12"),
          ("float", self.comparable, "12.3"),
          ("negative float", self.comparable, "-12.3"),
          ("positive float", self.comparable, "+12.3"),
          ("point float", self.comparable, ".12"),
          ("negative point float", self.comparable, "-.12"),
          ("positive point float", self.comparable, "+.12"),
          ("variable", self.comparable, "shoes_var"),
          ("dquote string", self.comparable, "\"shoes_str\""),
          ("squote string", self.comparable, "'shoes_str'"),
        
          ("var eq int", self.exp_comparison, "shoes_var == 12"),
          ("var eq string", self.exp_comparison, "shoes_var == \"23 foo fnord\""),
          ("string eq string", self.exp_comparison, "\"shoes_str\" == \"23 foo fnord\""),
          ("String ne int", self.exp_comparison, "\"shoes_str\" != 23"),
          ("var ge int", self.exp_comparison, "shoes_var >= 23"),
          ("var le int", self.exp_comparison, "shoes_var <= 23"),
          ("var gt int", self.exp_comparison, "shoes_var > 23.0"),
          ("var lt int", self.exp_comparison, "shoes_var < 23.0"),
        
          ("var lt float", self.exp_boolean, "shoes_var < 23.0"),
        
          ("bool true", self.comparable, "true"),
          ("bool false", self.comparable, "false"),
          ("bool var lt float", self.exp_boolean, "(shoes_var < 23.0)"),
        
          ("true expression", self.expression, '"true"'),
          ("comparison expression", self.expression, 'foo == "bar"'),
          ("complex expression", self.expression, '(shoes_var == "\\"3.0") or foo > 99 or "shambone" == "boolaroo" and not (gribble != "shoes" or 23 == 32)'),
        
        )
        
        
        teststr = "(A == B or C == D)  or E > 5 AND F == G or (H == 1 or b == 'foo')"
        testvars = {
            'A' : 5,
            'B' : 5,
            'C' : 's',
            'D' : 'q',
            'E' : 90,
            'F' : 'x',
            'G' : 'y',
            'H' : 10,
            'b' : 'afoo',
        }
        print(teststr)
        from pprint import pprint
        pprint(self.expression.parseString(teststr))
        rule = self.expression.parseString(teststr)[0]
        print rule

        print rule.evaluate(testvars)
        
        for testname, tester, test in tests:
            try:
                print "[PASS] "+testname + ": " + test + ": " + str(tester.parseString(test))
            except ParseException as e:
                print "[FAIL] "+testname + ": " + test + ": "+str(e)

if __name__ == '__main__':
    parser = QuenbRuleParser()
    parser.test()

