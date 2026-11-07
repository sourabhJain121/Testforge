import ast

def count_string_literals(source: str) -> int:
    tree = ast.parse(source)
    count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            count += 1
    return count
