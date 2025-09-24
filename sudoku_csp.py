# sudoku_csp.py
from typing import List, Tuple, Optional
import copy
import time

# ----------------------------
# CSP Components: Variables, Domain, Constraints
# ----------------------------

def get_variables() -> List[Tuple[int, int]]:
    """Return list of variables (row, column) for 9x9 Sudoku."""
    return [(row, column) for row in range(9) for column in range(9)]

def get_domain(grid: List[List[int]], var: Tuple[int, int]) -> List[int]:
    """Return domain for a given variable (cell). If already filled -> fixed domain. Else -> 1-9."""
    row, column = var
    if grid[row][column] != 0:
        return [grid[row][column]]
    return list(range(1, 10))

def check_constraint(grid: List[List[int]], var: Tuple[int, int], value: int) -> bool:
    """Check CSP constraints (row, column, box). Skip the cell itself when scanning."""
    row, column = var

    # Row constraint (skip the cell itself)
    for column_index in range(9):
        if column_index == column:
            continue
        if grid[row][column_index] == value:
            return False

    # Column constraint (skip the cell itself)
    for row_index in range(9):
        if row_index == row:
            continue
        if grid[row_index][column] == value:
            return False

    # Box constraint (3x3) (skip the cell itself)
    box_start_row, box_start_column = (row // 3) * 3, (column // 3) * 3
    for box_row_index in range(box_start_row, box_start_row + 3):
        for box_column_index in range(box_start_column, box_start_column + 3):
            if box_row_index == row and box_column_index == column:
                continue
            if grid[box_row_index][box_column_index] == value:
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

# instrumentation counters (module-level)
assignments_count = 0
backtracks_count = 0

def backtrack_solve(grid: List[List[int]]) -> Optional[List[List[int]]]:
    """Backtracking CSP solver for Sudoku (simple, first-empty selection)."""
    global assignments_count, backtracks_count

    variable = select_unassigned_variable(grid)
    if not variable:
        return grid  # solved

    row, column = variable
    for value in get_domain(grid, variable):
        if check_constraint(grid, variable, value):
            # assign
            grid[row][column] = value
            assignments_count += 1

            result = backtrack_solve(grid)
            if result is not None:
                return result

            # undo
            grid[row][column] = 0
            backtracks_count += 1

    return None

# ----------------------------
# Print Sudoku
# ----------------------------
def print_grid(grid: List[List[int]]):
    for row_index in range(9):
        row_str = ""
        for column_index in range(9):
            val = grid[row_index][column_index]
            row_str += str(val) if val != 0 else "."
            if column_index in (2, 5):
                row_str += " | "
            else:
                row_str += " "
        print(row_str)
        if row_index in (2, 5):
            print("-" * 21)
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

    # reset counters and run
    assignments_count = 0
    backtracks_count = 0
    start_time = time.perf_counter()
    solution = backtrack_solve(copy.deepcopy(puzzle))
    elapsed_time = time.perf_counter() - start_time

    if solution:
        print("=== Solved puzzle ===")
        print_grid(solution)
    else:
        print("No solution found.")

    print(f"Assignments: {assignments_count}, Backtracks: {backtracks_count}, Time: {elapsed_time:.4f}s")
