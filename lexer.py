# from http://stackoverflow.com/questions/133886/simple-regex-based-lexer-in-python
# under CC-WIKI license, so this is attribution. Thanks guys!
from __future__ import print_function

import sys
import re

class Token(object):
    """ A simple Token structure.
        Contains the token type, value and position. 
    """
    def __init__(self, type, val, pos):
        self.type = type
        self.val = val
        self.pos = pos

    def __repr__(self):
        return 'Token({0.type!r}, {0.val!r}, {0.pos!r})'.format(self)


class LexerError(Exception):
    """ Lexer error exception.

        pos:
            Position in the input line where the error occurred.
    """
    def __init__(self, pos):
        self.pos = pos


class Lexer(object):
    """ A simple regex-based lexer/tokenizer.

        See below for an example of usage.
    """
    def __init__(self, rules, skip_whitespace=True):
        """ Create a lexer.

            rules:
                A list of rules. Each rule is a `regex, type`
                pair, where `regex` is the regular expression used
                to recognize the token and `type` is the type
                of the token to return when it's recognized.

            skip_whitespace:
                If True, whitespace (\s+) will be skipped and not
                reported by the lexer. Otherwise, you have to 
                specify your rules for whitespace, or it will be
                flagged as an error.
        """
        self.rules = []

        for regex, type in rules:
            self.rules.append((re.compile(regex), type))

        self.skip_whitespace = skip_whitespace
        self.re_ws_skip = re.compile('\S')

    def input(self, buf):
        """ Initialize the lexer with a buffer as input.
        """
        self.buf = buf
        self.pos = 0

    def token(self):
        """ Return the next token (a Token object) found in the 
            input buffer. None is returned if the end of the 
            buffer was reached. 
            In case of a lexing error (the current chunk of the
            buffer matches no rule), a LexerError is raised with
            the position of the error.
        """
        if self.pos >= len(self.buf):
            return None
        else:
            if self.skip_whitespace:
                m = self.re_ws_skip.search(self.buf[self.pos:])

                if m:
                    self.pos += m.start()
                else:
                    return None

            for token_regex, token_type in self.rules:
                m = token_regex.match(self.buf[self.pos:])

                if m:
                    value = self.buf[self.pos + m.start():self.pos + m.end()]
                    tok = Token(token_type, value, self.pos)
                    self.pos += m.end()
                    return tok

            # if we're here, no rule matched
            raise LexerError(self.pos)

    def tokens(self):
        """ Returns an iterator to the tokens found in the buffer.
        """
        while 1:
            tok = self.token()
            if tok is None: break
            yield tok


if __name__ == '__main__':
    rules = [
        ('\d+',             'NUMBER'),
        ('[a-zA-Z_]\w+',    'IDENTIFIER'),
        ('\+',              'PLUS'),
        ('\-',              'MINUS'),
        ('\*',              'MULTIPLY'),
        ('\/',              'DIVIDE'),
        ('\(',              'LP'),
        ('\)',              'RP'),
        ('=',               'EQUALS'),
    ]

    lx = Lexer(rules, skip_whitespace=True)
    lx.input('erw = _abc + 12*(R4-623902)  ')

    try:
        for tok in lx.tokens():
            print(tok)
    except LexerError, err:
        print('LexerError at position', err.pos)
