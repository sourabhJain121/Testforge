from typing import List

def transpose_matrix(matrix: List[List[float]]) -> List[List[float]]:
    if not matrix or not matrix[0]:
        return []
    return [[row[i] for row in matrix] for i in range(len(matrix[0]))]
