# sudoku_csp.py
from typing import List, Tuple, Optional, Dict
import copy
import time

# ----------------------------
# CSP Components: Variables, Domain, Constraints
# ----------------------------

Variable = Tuple[int, int]
Grid = List[List[int]]

def get_variables() -> List[Variable]:
    """Return list of variables (row, column) for 9x9 Sudoku."""
    return [(row, column) for row in range(9) for column in range(9)]

def get_domain(grid: Grid, var: Variable) -> List[int]:
    """Return domain for a given variable (cell). If already filled -> fixed domain. Else -> 1-9."""
    row, column = var
    if grid[row][column] != 0:
        return [grid[row][column]]
    return list(range(1, 10))

def check_constraint(grid: Grid, var: Variable, value: int) -> bool:
    """Check CSP constraints (row, column, box). Skip the cell itself when scanning."""
    row, column = var

    # Row constraint (skip the cell itself)
    for peer_column in range(9):
        if peer_column == column:
            continue
        if grid[row][peer_column] == value:
            return False

    # Column constraint (skip the cell itself)
    for peer_row in range(9):
        if peer_row == row:
            continue
        if grid[peer_row][column] == value:
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
# Forward checking helpers (NEW)
# ----------------------------
def initial_domains(grid: Grid) -> Dict[Variable, List[int]]:
    """
    Build initial domains for each variable:
    - assigned cells -> [value]
    - unassigned cells -> [1..9] minus values already present in peers
    """
    domains: Dict[Variable, List[int]] = {}
    for row in range(9):
        for column in range(9):
            variable = (row, column)
            if grid[row][column] != 0:
                domains[variable] = [grid[row][column]]
            else:
                # start with all values then prune those seen in peers
                possible_values = list(range(1, 10))
                # remove values that are already present in the row
                used_in_row = {grid[row][peer_column] for peer_column in range(9) if grid[row][peer_column] != 0}
                # remove values that are already present in the column
                used_in_column = {grid[peer_row][column] for peer_row in range(9) if grid[peer_row][column] != 0}
                # remove values that are already present in the 3x3 box
                box_start_row, box_start_column = (row // 3) * 3, (column // 3) * 3
                used_in_box = {
                    grid[box_row_index][box_column_index]
                    for box_row_index in range(box_start_row, box_start_row + 3)
                    for box_column_index in range(box_start_column, box_start_column + 3)
                    if grid[box_row_index][box_column_index] != 0
                }
                used_values = used_in_row.union(used_in_column).union(used_in_box)
                domains[variable] = [v for v in possible_values if v not in used_values]
    return domains

def peers_of(var: Variable) -> List[Variable]:
    """Return list of peer coordinates that share row, column, or 3x3 box with var (excluding var)."""
    row, column = var
    peers: List[Variable] = []

    # row peers
    for peer_column in range(9):
        if peer_column != column:
            peers.append((row, peer_column))

    # column peers
    for peer_row in range(9):
        if peer_row != row:
            peers.append((peer_row, column))

    # box peers
    box_start_row, box_start_column = (row // 3) * 3, (column // 3) * 3
    for box_row_index in range(box_start_row, box_start_row + 3):
        for box_column_index in range(box_start_column, box_start_column + 3):
            if (box_row_index, box_column_index) != var and (box_row_index, box_column_index) not in peers:
                peers.append((box_row_index, box_column_index))

    return peers

def forward_check(assign_variable: Variable, assigned_value: int, domains: Dict[Variable, List[int]], grid: Grid) -> Optional[List[Tuple[Variable, int]]]:
    """
    Perform forward checking after assigning assign_variable = assigned_value.
    Remove assigned_value from domains of unassigned peers.
    Return a list of (peer_variable, removed_value) so caller can undo them on backtrack.
    If any peer domain becomes empty, return None to indicate failure.
    """
    pruned_list: List[Tuple[Variable, int]] = []

    for peer in peers_of(assign_variable):
        peer_row, peer_column = peer
        if grid[peer_row][peer_column] != 0:
            # already assigned in grid
            continue
        if assigned_value in domains.get(peer, []):
            domains[peer].remove(assigned_value)
            pruned_list.append((peer, assigned_value))
            if not domains[peer]:
                # domain wiped out -> failure
                return None

    return pruned_list

def undo_pruning(pruned_list: List[Tuple[Variable, int]], domains: Dict[Variable, List[int]]):
    """Undo the domain removals recorded in pruned_list."""
    # restore in reverse order for clarity (not strictly necessary)
    for variable, removed_value in reversed(pruned_list):
        if removed_value not in domains[variable]:
            domains[variable].append(removed_value)

# ----------------------------
# CSP Backtracking Solver (with forward checking only)
# ----------------------------

def select_unassigned_variable(grid: Grid) -> Optional[Variable]:
    """Find next unassigned variable (empty cell) - first empty cell (no MRV)."""
    for row in range(9):
        for column in range(9):
            if grid[row][column] == 0:
                return (row, column)
    return None

# instrumentation counters
assignments_count = 0
backtracks_count = 0

def backtrack_solve(grid: Grid, domains: Dict[Variable, List[int]]) -> Optional[Grid]:
    """
    Backtracking solver that uses forward checking.
    domains must be the current domains for each variable (kept up-to-date).
    """
    global assignments_count, backtracks_count

    variable = select_unassigned_variable(grid)
    if not variable:
        return grid  # solved

    row, column = variable
    # iterate domain values from domains dict (deterministic order)
    for value in list(domains[variable]):
        if check_constraint(grid, variable, value):
            # assign
            grid[row][column] = value
            assignments_count += 1

            # save domain state for this variable (so undo sets it back to single value)
            saved_domain_for_variable = domains[variable]
            domains[variable] = [value]

            # forward check: prune peers' domains
            pruned = forward_check(variable, value, domains, grid)
            if pruned is not None:
                # continue search
                result = backtrack_solve(grid, domains)
                if result is not None:
                    return result
                # undo deeper failure's prunings already handled by deeper returns/undos
            # undo: restore pruned values (if any)
            if pruned is not None:
                undo_pruning(pruned, domains)
            # undo assignment and restore domain
            grid[row][column] = 0
            domains[variable] = saved_domain_for_variable
            backtracks_count += 1

    return None

# ----------------------------
# Print Sudoku
# ----------------------------
def print_grid(grid: Grid):
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
    puzzle: Grid = [
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

    # build initial domains with simple pruning using peers' assigned values
    domains = initial_domains(copy.deepcopy(puzzle))

    # reset counters and run
    assignments_count = 0
    backtracks_count = 0
    start_time = time.perf_counter()
    solution = backtrack_solve(copy.deepcopy(puzzle), domains)
    elapsed_time = time.perf_counter() - start_time

    if solution:
        print("=== Solved puzzle ===")
        print_grid(solution)
    else:
        print("No solution found.")

    print(f"Assignments: {assignments_count}, Backtracks: {backtracks_count}, Time: {elapsed_time:.4f}s")
