import textwrap
from typing import List

def format_bullet_points(items: List[str], width: int = 60) -> str:
    wrapper = textwrap.TextWrapper(width=width, initial_indent='- ', subsequent_indent='  ')
    return '\n'.join(wrapper.fill(item) for item in items)
