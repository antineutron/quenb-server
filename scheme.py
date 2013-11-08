from __future__ import print_function

# from http://norvig.com/lispy.html
# Based on code by Peter Norvig <pnorvig@google.com>

# He said it could be licensed under any license I see fit.
# So I'm going to say it's under the MIT license.

#Copyright (C) 2013 Peter Norvig

#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# There are modifications on my part, but some of it was copy/paste
# although I like to think I've improved it

import re
import math
import operator
import collections
import traceback
import os
import random
import datetime
import numbers
import traceback
import copy

import lexer

Symbol = collections.namedtuple("Symbol", "value")
SpecialSymbol = collections.namedtuple("SpecialSymbol", "value")
Character = collections.namedtuple("Character", "value")

def evaluate_string(input_string, env=None):
    assert input_string

    if env is None:
        env = get_default_environment()

    if "\n" in input_string:
        multiline_string = input_string

        lines = []
        for line in multiline_string.split("\n"):
            line = line.strip()
            if ';' in line:
                line = line[:line.index(';')]

            if line:
                lines.append(line)

        assert lines

        code = "(begin {})".format(" ".join(lines))
        result = eval(parse(code), env)
    else:
        result = eval(parse(input_string), env)

    return result, env

def get_default_environment():
    env = Env()
    env.update(GLOBAL_ENV)
    return env

class Env(collections.MutableMapping):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    def __init__(self, parms=(), args=(), outer=None):
        self._dict = {}

        self._dict.update(zip(parms,args))
        self.outer = outer

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def __delitem__(self, key):
        del self._dict[key]

    def __iter__(self):
        return iter(self._dict)

    def __len__(self):
        return len(self._dict)

    def find(self, var):
        "Find the innermost Env where var appears."
        if var in self._dict:
            return self
        elif self.outer is None:
            raise SchemeAttributeException(var)
        else:
            return self.outer.find(var)
    def add_item(self, item):
        # Assume its an item like ('name', value)
        # Shouldn't be used by scheme, but external modules wanting to insert
        # values into the environment

        self._dict[Symbol(item[0])] = item[1]


# Standard procedures
procedures = {}

def _eqv_predicate(obj1, obj2):
    if obj1 == True and obj2 == True:
        return True
    elif obj1 == False and obj2 == False:
        return True
    elif type(obj1) == Symbol and type(obj2) == Symbol and obj1 == obj2:
        return True
    elif type(obj1) == int and type(obj2) == int and obj1 == obj2:
        return True
    elif type(obj1) == Character and type(obj2) == Character and obj1 == obj2:
        return True
    elif obj1 == [] and obj2 == []:
        return True

procedures['eqv?'] = _eqv_predicate
procedures['equal?'] = operator.eq

# Numberical types
# number
#    complex
#    real
#    rational
#    integer

procedures['number?'] = lambda obj: type(obj) in (int, complex, float)
procedures['complex?'] = lambda obj: type(obj) == complex
procedures['real?'] = lambda obj: None # FIXME don't really understand the numerical types
procedures['rational?'] = lambda obj: None
procedures['integer?'] = lambda obj: type(obj) == int

procedures['exact?'] = lambda z: None
procedures['inexact?'] = lambda z: None

procedures['inexact->exact'] = lambda num: int(num)
procedures['exact->inexact'] = lambda num: float(num)

def _comparing(cmp):
    def inner(*args):
        args = list(args)
        while len(args) >= 2:
            a, b = args[0], args[1]
            result = cmp(a, b)
            if not result:
                return False
            args.pop(0)

        return True

    return inner

procedures['='] = _comparing(operator.eq)
procedures['<'] = _comparing(operator.lt)
procedures['>'] = _comparing(operator.gt)
procedures['<='] = _comparing(operator.le)
procedures['>='] = _comparing(operator.ge)

procedures['zero?'] = lambda z: z == 0
procedures['positive?'] = lambda x: x >= 0
procedures['negative?'] = lambda x: x <= 0
procedures['odd?'] = lambda n: n % 2 != 0
procedures['even?'] = lambda n: n % 2 == 0

procedures['max'] = lambda *x: max(x)
procedures['min'] = lambda *x: min(x)

def _scheme_add(*z):
    if not z:
        return 0
    else:
        total = 0
        for number in z:
            total += number
        return total

procedures['+'] = _scheme_add

def _scheme_mul(*z):
    if not z:
        return 1
    else:
        value = 1
        for number in z:
            value *= number
        return value

procedures['*'] = _scheme_mul

def _scheme_sub(*z):
    if len(z) == 1:
        return 0 - z[0]
    else:
        value = z[0]
        for i in range(1,len(z)):
            value -= z[i]
        return value

procedures['-'] = _scheme_sub

def _scheme_div(*z):
    if len(z) == 1:
        # FIXME Returns a float, when we should really have accuracy and fractions
        return 1.0 / z[0]
    else:
        value = z[0]
        for i in range(1,len(z)):
            value /= z[i]
        return value

procedures['/'] = _scheme_div
procedures['abs'] = lambda x: abs(x)
procedures['quotient'] = lambda n1, n2: n1 // n2
procedures['remainder'] = lambda n1, n2: None # FIXME remainder not implemented
procedures['modulo'] = lambda n1, n2: n1 % n2

procedures['gcd'] = lambda *n: None # FIXME gcd for multiple numbers
procedures['lcm'] = lambda *n: None

# Also some more maths stuff, but w/e

procedures['floor'] = lambda x: int(math.floor(x))
procedures['ceiling'] = lambda x: int(math.ceil(x))
procedures['truncate'] = lambda x: int(math.trunc(x))
# TODO round - not sure what the definition is

def _scheme_number_to_string(z, radix=10):
    assert radix in (2,8,10,16)
    if radix == 10:
        return str(z)
    elif radix == 2:
        return bin(z)
    elif radix == 8:
        return oct(z)
    elif radix == 16:
        return hex(z)

procedures['number->string'] = _scheme_number_to_string

def _scheme_string_to_number(string, radix=10):
    return int(string, radix)

procedures['string->number'] = _scheme_string_to_number

procedures['not'] = operator.not_
procedures['boolean?'] = lambda obj: type(obj) == bool

# Pairs and lists, skipping most of this stuff

procedures['car'] = lambda pair: pair[0]
procedures['cdr'] = lambda pair: pair[1:]

def _scheme_cons(obj1, obj2):
    L = [obj1]
    L.extend(copy.deepcopy(obj2))
    return L


procedures['cons'] = _scheme_cons

# I can't believe I typed these by hand
_compositions = (
    'aa', 'ad', 'da', 'dd', 'aaa', 'aad', 'ada', 'add', 'daa', 'dad', 'dda',
    'ddd', 'aaaa', 'aaad', 'aada', 'aadd', 'adaa', 'adad', 'adda', 'addd',
    'daaa', 'daad', 'dada', 'dadd', 'ddaa', 'ddad', 'ddda', 'dddd'
)

for item in _compositions:
    expr = 'lambda pair: pair'
    for letter in item:
        if letter == 'a':
            expr += '[0]'
        else:
            expr += '[1:]'

    # I just used eval in code, please forgive me, I'm so sorry
    func = eval(expr)
    procedures['c' + item + 'r'] = func

procedures['null?'] = lambda obj: obj == []
procedures['list?'] = lambda obj: type(obj) == list
procedures['list'] = lambda *objs: list(objs)
procedures['length'] = lambda list_: len(list_)
procedures['append'] = lambda *lists: list(itertools.chain(*lists))
procedures['reverse'] = lambda list_: list(reverse(list_))
procedures['list-tail'] = lambda list_, k: list_[k:]
procedures['list-ref'] = lambda list_, k: list_[k]

def _scheme_member(obj, list_):
    if obj in list_:
        index = list_.index(obj)
        return list_[index:]
    else:
        return False

procedures['member'] = _scheme_member

def _scheme_assoc(obj, alist):
    for pair in alist:
        if pair[0] == obj:
            return pair
    return False

procedures['assoc'] = _scheme_assoc

procedures['symbol?'] = lambda obj: type(obj) == Symbol
procedures['symbol->string'] = lambda symbol: str(symbol.value)
procedures['string->symbol'] = lambda string: Symbol(string)
procedures['string-length'] = lambda string: len(string)
procedures['string-ref'] = lambda string, k: Character(string[k])
procedures['string->list'] = lambda string: [Character(s) for s in string]
procedures['substring'] = lambda string, start, end: string[start:end]
procedures['string-append'] = lambda *strings: "".join(strings)

procedures['procedure?'] = lambda obj: hasattr(obj, '__call__')

def _scheme_apply(proc, *args):
    assert len(args)
    final_arg = args[-1]
    # The final arg must be a list
    other_args = list(args[:-1])

    args = other_args + final_arg
    return proc(args)

procedures['apply'] = _scheme_apply

procedures['map'] = map

GLOBAL_ENV = Env()
for item in procedures.items():
    GLOBAL_ENV.add_item(item)

def eval(x, env=None):
    if env is None:
        env = get_default_environment()

    "Evaluate an expression in an environment."
    try:
        if isa(x, Symbol):             # variable reference
            return env.find(x)[x]
        elif not isa(x, list):         # constant literal
            return x
        elif x[0] == Symbol('quote'):          # (quote exp)
            (_, exp) = x
            return exp
        elif x[0] == Symbol('if'):             # (if test conseq alt)
            (_, test, conseq, alt) = x
            return eval((conseq if eval(test, env) else alt), env)
        elif x[0] == Symbol('set!'):           # (set! var exp)
            (_, var, exp) = x
            env.find(var)[var] = eval(exp, env)
        elif x[0] == Symbol('define'):         # (define var exp)
            (_, var, exp) = x
            env[var] = eval(exp, env)
        elif x[0] == Symbol('lambda'):         # (lambda (var*) exp)
            vars = x[1]
            exps = x[2:]
            assert len(exps)

            # (lambda <variable> <body>)
            if isa(vars, Symbol):
                def func(*args):
                    e = Env([vars], [list(args)], env)
                    for exp in exps:
                        val = eval(exp, e)
                    return val
                return func
            # (lambda (<variable 1> ... <variable n> . <variable n+1>) <body>)
            elif SpecialSymbol('.') in vars:
                index = vars.index(SpecialSymbol('.'))
                first_bunch = vars[:index]
                rest_symbol = vars[index + 1]
                def func(*args):
                    args = list(args)

                    e = Env(outer=env)

                    for symbol in first_bunch:
                        e[symbol] = args.pop(0)

                    e[rest_symbol] = args

                    for exp in exps:
                        val = eval(exp, e)
                    return val
                return func
            else:
                def func(*args):
                    e = Env(vars, args, env)
                    for exp in exps:
                        val = eval(exp, e)
                    return val
                return func

        elif x[0] == Symbol('begin'):          # (begin exp*)
            for exp in x[1:]:
                val = eval(exp, env)
            return val
        elif x[0] == Symbol('cond'):           # (cond clause*)
            for clause in x[1:]:
                # Each clause has the form (predicate expression ...)
                if clause[0] == Symbol('else'):
                    for exp in clause[1:]:
                        val = eval(exp, env)
                    return val
                else:
                    predicate = eval(clause[0], env)
                    if predicate:
                        for exp in clause[1:]:
                            val = eval(exp, env)
                        return val
        elif x[0] == Symbol('and'):
            some_expressions = False

            for exp in x[1:]:
                some_expressions = True
                val = eval(exp, env)
                # FIXME change to scheme truthiness, not python truthiness
                if not val:
                    return val
            return val if some_expressions else True

        elif x[0] == Symbol('or'):
            some_expressions = False

            for exp in x[1:]:
                some_expressions = True

                val = eval(exp, env)
                # FIXME scheme truth
                if val:
                    return val
            return val if some_expressions else False


        elif x[0] == Symbol('quasiquote'):
            qq_template = x[1]
            result = []
            for item in qq_template:
                if isa(item, list) and item[0] == Symbol('unquote'):
                    val = eval(item[1], env)
                else:
                    val = item
                result.append(val)
            return result
        else:                          # (proc exp*)
            exps = [eval(exp, env) for exp in x]
            proc = exps.pop(0)
            return proc(*exps)
    except SchemeException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise SchemeRuntimeException(e)


isa = isinstance


def parse(str):
    try:
        tokens = tokenize(str)
    except lexer.LexerError as e:
        traceback.print_exc()
        raise SchemeSyntaxError(e)

    return read_from(tokens)

def tokenize(str):
    """Given a string, break it into a list structure"""
    # Can throw lexer.LexerError
    rules = [
        (r'[-+]?\d+\.\d+',  'FLOAT'),
        (r'[-+]?\d+',        'INTEGER'),

        (r'[a-zA-Z=*+/<>!\?][a-zA-Z0-9=*+/<>!\?-]*', 'IDENTIFIER'),

        (r'[\+\-\*\/]',      'MATHS'),
        (r'\(',              'LP'),
        (r'\)',              'RP'),
        (r'\.',              'PERIOD'),
        (r"""'""",           'QUOTE'),
        (r"""`""",           'BACKQUOTE'),
        (r',',             'COMMA'),
        (r'\".*?\"',        'STRING'),
        (r'#[tf]',          'BOOLEAN'),
    ]
    lx = lexer.Lexer(rules, skip_whitespace=True)
    lx.input(str)
    return list(lx.tokens())

def read_from(tokens):
    if not tokens:
        raise SchemeSyntaxError("Unexpected EOF")

    token = tokens.pop(0)
    if token.type == 'LP':
        L = []
        while tokens[0].type != 'RP':
            L.append(read_from(tokens))
        tokens.pop(0) # pop off ')'
        return L
    elif token.type == 'RP':
        raise SyntaxError("Unexpected )")
    elif token.type == 'QUOTE':
        return [Symbol("quote"), read_from(tokens)]
    elif token.type == 'COMMA':
        return [Symbol("unquote"), read_from(tokens)]
    elif token.type == 'BACKQUOTE':
        return [Symbol("quasiquote"), read_from(tokens)]

    else:
        return atom(token)

def atom(token):
    try:
        if token.type == 'FLOAT':
            return float(token.val)
        elif token.type == 'IDENTIFIER' or token.type == 'MATHS':
            return Symbol(token.val)
        elif token.type == 'INTEGER':
            return int(token.val)
        elif token.type == 'STRING':
            # Chop the " bits off.
            return str(token.val[1:-1])
        elif token.type == 'BOOLEAN':
            if token.val == '#t':
                return True
            elif token.val == '#f':
                return False
        elif token.type == 'PERIOD':
            return SpecialSymbol('.')

    except ValueError as e:
        raise SchemeSyntaxError("Bad token type. Bug?")

def to_string(exp):
    "Convert a Python object back into a Lisp-readable string."
    if isinstance(exp, list):
        return '(' + ' '.join(map(to_string, exp)) + ')'
    else:
        return repr(exp)

def repl(prompt='lis.py> '):
    "A prompt-read-eval-print loop."
    env = Env()
    env.update(GLOBAL_ENV)

    while True:
        try:
            text = raw_input(prompt)
        except EOFError:
            print()
            break

        if not text:
            print()
            break

        try:
            val = eval(parse(text), env)
            if val is not None:
                print(to_string(val))
        except SchemeException as e:
            traceback.print_exc()


class SchemeException(Exception):
    pass

class SchemeRuntimeException(SchemeException):
    pass

class SchemeSyntaxError(SchemeException):
    pass


class SchemeAttributeException(SchemeException):
    pass

S = Symbol

def test_scheme():
    assert eval(2) == 2
    assert eval(3.0) == 3.0
    assert eval([S('if'), False, 4, 5]) == 5
    assert eval([S('+'), 6, 7]) == 13
    assert eval([S('begin'), [S('define'), S('a'), 8], S('a')]) == 8

    assert parse("2") == 2
    assert parse("3.0") == 3.0
    assert parse("(1 2 3)") == [1,2,3]
    assert parse("(a b c)") == [S("a"), S("b"), S("c")]
    assert parse("(if #f 4 5)") == [S("if"), False, 4, 5]

def test_complexfunctions():
    string = """(define string-ishex?
     (lambda (string)
        (cond
       ((= 0 (string-length string)) #f)
       ((= 1 (string-length string)) (char-ishex? (string-ref string 0)))
       (else (and
                (char-ishex? (string-ref string 0))
                (string-ishex? (substring string 1 (string-length string)))
             )
       )
      )
     )
    )

    (define char-ishex?
     (lambda (char)
        (member char (string->list "0123456789abcdef"))
     )
    )"""
    result, env = evaluate_string(string)
    assert not evaluate_string('''(string-ishex? "")''', env)[0]
    assert not evaluate_string('''(string-ishex? "nothex")''', env)[0]
    assert evaluate_string('''(string-ishex? "abc")''', env)[0]
    assert evaluate_string('''(string-ishex? "378234bcbc")''', env)[0]
    assert not evaluate_string('''(string-ishex? "3782X34bcbcX")''', env)[0]

def test_and():
    e = evaluate_string
    assert e("(and 1 2 3)")[0] == 3
    assert not e("(and #f invalid-symbol also-invalid)")[0]
