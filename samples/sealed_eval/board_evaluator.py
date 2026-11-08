"""
samples/sealed_eval/board_evaluator.py

Domain: Game Logic & State Evaluation
Evaluates board states, moves, and victory conditions for grid-based turn games.
"""

from typing import List, Optional, Tuple


def create_board(size: int = 3) -> List[List[str]]:
    """Initializes an empty N x N grid with empty cells ' '."""
    if size < 3 or size > 10:
        raise ValueError("Board size must be between 3 and 10.")
    return [[" " for _ in range(size)] for _ in range(size)]


def make_move(board: List[List[str]], row: int, col: int, player: str) -> bool:
    """Places player token ('X' or 'O') at (row, col) if empty and in-bounds."""
    if player not in ("X", "O"):
        raise ValueError("Player must be 'X' or 'O'.")

    size = len(board)
    if row < 0 or row >= size or col < 0 or col >= size:
        return False

    if board[row][col] != " ":
        return False

    board[row][col] = player
    return True


def check_winner(board: List[List[str]]) -> Optional[str]:
    """
    Checks horizontal, vertical, and diagonal lines for winning run.
    Returns winning player ('X' or 'O') or None.
    """
    size = len(board)
    if size < 3:
        return None

    # Horizontal check
    for r in range(size):
        first = board[r][0]
        if first != " " and all(board[r][c] == first for c in range(size)):
            return first

    # Vertical check
    for c in range(size):
        first = board[0][c]
        if first != " " and all(board[r][c] == first for r in range(size)):
            return first

    # Main diagonal
    diag1_first = board[0][0]
    if diag1_first != " " and all(board[i][i] == diag1_first for i in range(size)):
        return diag1_first

    # Anti-diagonal
    diag2_first = board[0][size - 1]
    if diag2_first != " " and all(board[i][size - 1 - i] == diag2_first for i in range(size)):
        return diag2_first

    return None


def is_board_full(board: List[List[str]]) -> bool:
    """Returns True if there are zero unoccupied cells remaining."""
    for row in board:
        for cell in row:
            if cell == " ":
                return False
    return True


def get_available_moves(board: List[List[str]]) -> List[Tuple[int, int]]:
    """Returns list of (row, col) tuples that are currently unoccupied."""
    moves = []
    size = len(board)
    for r in range(size):
        for c in range(size):
            if board[r][c] == " ":
                moves.append((r, c))
    return moves
