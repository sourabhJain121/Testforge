"""Pure Python simple shell-style command line tokenizer from CPython shlex.py"""

def simple_shlex_split(s: str) -> list[str]:
    """Split the string s using shell-like syntax."""
    tokens = []
    current_token = []
    in_quote = False
    quote_char = ''
    escaped = False

    for char in s:
        if escaped:
            current_token.append(char)
            escaped = False
            continue
        if char == '\\':
            escaped = True
            continue
        if char in ('"', "'"):
            if not in_quote:
                in_quote = True
                quote_char = char
            elif quote_char == char:
                in_quote = False
                quote_char = ''
            else:
                current_token.append(char)
            continue
        if char.isspace() and not in_quote:
            if current_token:
                tokens.append(''.join(current_token))
                current_token = []
            continue
        current_token.append(char)

    if in_quote:
        raise ValueError('No closing quotation')
    if escaped:
        raise ValueError('Trailing backslash')
    if current_token:
        tokens.append(''.join(current_token))
    return tokens
