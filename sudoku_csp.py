# sudoku_csp.py
from typing import List, Tuple, Optional
import copy

# ----------------------------
# CSP Components: Variables, Domain, Constraints
# ----------------------------

def get_variables() -> List[Tuple[int, int]]:
    """Return list of variables (row, col) for 9x9 Sudoku. It's going to 81 variable which represent each cell."""
    return [(row, column) for row in range(9) for column in range(9)]

def get_domain(grid: List[List[int]], var: Tuple[int, int]) -> List[int]:
    """Return domain for a given variable (cell). If already filled -> fixed domain. Else -> 1-9."""
    row, column = var
    if grid[row][column] != 0:
        return [grid[row][column]]
    return list(range(1, 10))

def check_constraint(grid: List[List[int]], var: Tuple[int, int], value: int) -> bool:
    """Check CSP constraints (row, col, box)."""
    row, column = var

    # Constraint 1: Each row should have all the values from 1 to 9 without repeatetions
    if any(grid[row][column_index] == value for column_index in range(9)):
        return False

    # Constraint 2: Each column should have all the values from 1 to 9 without repeatetions
    if any(grid[row_index][column] == value for row_index in range(9)):
        return False
    
    # Constraint 3: Each box of 3*3 should have all the values from 1 to 9 without repeatetions
    box_row, box_column = (row // 3) * 3, (column // 3) * 3
    for row in range(box_row, box_row+3):
        for column in range(box_column, box_column+3):
            if grid[row][column] == value:
                return False

    return True

# ----------------------------
# CSP Backtracking Solver
# ----------------------------

def select_unassigned_variable(grid: List[List[int]]) -> Optional[Tuple[int, int]]:
    """Find next unassigned variable (empty cell)."""
    for row in range(9):
        for column in range(9):
            if grid[row][column] == 0:
                return (row, column)
    return None

def backtrack_solve(grid: List[List[int]]) -> Optional[List[List[int]]]:
    """Backtracking CSP solver for Sudoku."""
    variable = select_unassigned_variable(grid)
    if not variable:
        return grid  # solved
    
    row, column = variable
    for value in get_domain(grid, variable):
        if check_constraint(grid, variable, value):
            grid[row][column] = value
            result = backtrack_solve(grid)
            if result is not None:
                return result
            grid[row][column] = 0  # undo
    return None

# ----------------------------
# Print Sudoku
# ----------------------------
def print_grid(grid: List[List[int]]):
    for row_index in range(9):
        row = ""
        for column_index in range(9):
            val = grid[row_index][column_index]
            row += str(val) if val != 0 else "."
            if column_index in (2,5): row += " | "
            else: row += " "
        print(row)
        if row_index in (2,5): print("-"*21)
    print()

# ----------------------------
# Example Puzzle
# ----------------------------
if __name__ == "__main__":
    puzzle = [
        [5,3,0, 0,7,0, 0,0,0],
        [6,0,0, 1,9,5, 0,0,0],
        [0,9,8, 0,0,0, 0,6,0],

        [8,0,0, 0,6,0, 0,0,3],
        [4,0,0, 8,0,3, 0,0,1],
        [7,0,0, 0,2,0, 0,0,6],

        [0,6,0, 0,0,0, 2,8,0],
        [0,0,0, 4,1,9, 0,0,5],
        [0,0,0, 0,8,0, 0,7,9]
    ]

    print("=== Given puzzle ===")
    print_grid(puzzle)

    solution = backtrack_solve(copy.deepcopy(puzzle))
    if solution:
        print("=== Solved puzzle ===")
        print_grid(solution)
    else:
        print("No solution found.")
