"""
samples/expression_tokenizer.py - Real-World Mathematical & Logical Expression Tokenizer.
License: MIT
Author: TestForge Benchmark Suite
LOC: ~105 lines
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional


class TokenType(Enum):
    NUMBER = auto()
    IDENTIFIER = auto()
    OPERATOR = auto()
    STRING = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    position: int
    line: int = 1


class TokenizerError(ValueError):
    """Raised when encountering invalid lexical tokens or malformed strings."""
    def __init__(self, message: str, position: int):
        super().__init__(f"Lexical error at position {position}: {message}")
        self.position = position


class ExpressionTokenizer:
    """
    Lexical scanner for mathematical, boolean, and functional expressions.
    Supports integers, floats, identifiers, multi-character relational operators,
    and single/double quoted string literals.
    """
    MULTI_CHAR_OPS = {"==", "!=", "<=", ">=", "**", "&&", "||"}
    SINGLE_CHAR_OPS = set("+-*/%<>=!&|^~")

    def __init__(self, text: str):
        self.text = text or ""
        self.pos = 0
        self.length = len(self.text)

    def _peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        return self.text[idx] if idx < self.length else None

    def _advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        return ch

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            ch = self._peek()

            # 1. Skip whitespace
            if ch.isspace():
                self._advance()
                continue

            start_pos = self.pos

            # 2. Structural punctuation
            if ch == '(':
                tokens.append(Token(TokenType.LPAREN, self._advance(), start_pos))
            elif ch == ')':
                tokens.append(Token(TokenType.RPAREN, self._advance(), start_pos))
            elif ch == ',':
                tokens.append(Token(TokenType.COMMA, self._advance(), start_pos))

            # 3. Numeric literals (int & float)
            elif ch.isdigit() or (ch == '.' and (self._peek(1) or '').isdigit()):
                num_str = ""
                has_dot = False
                while self.pos < self.length:
                    curr = self._peek()
                    if curr.isdigit():
                        num_str += self._advance()
                    elif curr == '.' and not has_dot:
                        has_dot = True
                        num_str += self._advance()
                    else:
                        break
                tokens.append(Token(TokenType.NUMBER, num_str, start_pos))

            # 4. Identifiers & Keywords
            elif ch.isalpha() or ch == '_':
                ident = ""
                while self.pos < self.length and (self._peek().isalnum() or self._peek() == '_'):
                    ident += self._advance()
                tokens.append(Token(TokenType.IDENTIFIER, ident, start_pos))

            # 5. String literals
            elif ch in ('"', "'"):
                quote = self._advance()
                str_val = ""
                closed = False
                while self.pos < self.length:
                    curr = self._advance()
                    if curr == '\\' and self.pos < self.length:
                        str_val += self._advance()
                    elif curr == quote:
                        closed = True
                        break
                    else:
                        str_val += curr
                if not closed:
                    raise TokenizerError("Unterminated string literal", start_pos)
                tokens.append(Token(TokenType.STRING, str_val, start_pos))

            # 6. Multi-character and single-character operators
            elif ch in self.SINGLE_CHAR_OPS:
                two_char = self.text[self.pos:self.pos + 2]
                if two_char in self.MULTI_CHAR_OPS:
                    self.pos += 2
                    tokens.append(Token(TokenType.OPERATOR, two_char, start_pos))
                else:
                    tokens.append(Token(TokenType.OPERATOR, self._advance(), start_pos))

            else:
                raise TokenizerError(f"Unexpected character: {ch!r}", start_pos)

        tokens.append(Token(TokenType.EOF, "", self.pos))
        return tokens
