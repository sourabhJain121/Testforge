"""Pure Python TextWrap algorithms from CPython textwrap.py"""
import re

class TextWrapAlgo:
    """Basic text wrapping algorithm wrapping strings to fixed column widths."""
    wordsep_re = re.compile(r'(\s+)')

    def __init__(self, width: int = 70):
        if width <= 0:
            raise ValueError(f'invalid width {width!r} (must be > 0)')
        self.width = width

    def split_words(self, text: str) -> list[str]:
        chunks = self.wordsep_re.split(text)
        return [c for c in chunks if c]

    def wrap(self, text: str) -> list[str]:
        chunks = self.split_words(text)
        lines: list[str] = []
        cur_line: list[str] = []
        cur_len = 0

        for chunk in chunks:
            chunk_len = len(chunk)
            if chunk.isspace():
                if cur_line:
                    cur_line.append(chunk)
                    cur_len += chunk_len
                continue

            if cur_len + chunk_len <= self.width:
                cur_line.append(chunk)
                cur_len += chunk_len
            else:
                if cur_line:
                    lines.append(''.join(cur_line).rstrip())
                    cur_line = []
                    cur_len = 0
                cur_line.append(chunk)
                cur_len += chunk_len

        if cur_line:
            lines.append(''.join(cur_line).rstrip())
        return lines

    def fill(self, text: str) -> str:
        return "\n".join(self.wrap(text))
