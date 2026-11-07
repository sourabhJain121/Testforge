import bisect

GRADE_CUTOFFS = [60, 70, 80, 90]
GRADE_LETTERS = ['F', 'D', 'C', 'B', 'A']

def assign_letter_grade(score: int) -> str:
    idx = bisect.bisect(GRADE_CUTOFFS, score)
    return GRADE_LETTERS[idx]
