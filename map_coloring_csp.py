# india_csp.py
from typing import List, Dict, Tuple, Optional
import geopandas as gpd
import matplotlib.pyplot as plt
import copy
import time

# ----------------------------
# Config
# ----------------------------
GEOJSON_PATH = "india_states_geoboundaries.geojson"   # path to India states GeoJSON
# extended palette (8 colors)
COLOR_PALETTE: List[str] = ["#e31a93", "#ffff00", "#1f78b4", "#33a02c", "#e31a1c", "#ff7f00"]

# ----------------------------
# Types
# ----------------------------
Variable = str     # state name
Color = str
Adjacency = Dict[Variable, List[Variable]]
Domains = Dict[Variable, List[Color]]

# ----------------------------
# Load geojson and build adjacency
# ----------------------------
def detect_state_name_column(geo_dataframe: gpd.GeoDataFrame) -> str:
    """Pick a plausible column name that contains state names."""
    candidate_columns = [
        "st_nm", "STATE_NAME", "NAME_1", "NAME", "state", "STATE", "st_name",
        "shapeName", "shape_group", "shapeGroup", "shapeName_1"
    ]
    for candidate in candidate_columns:
        if candidate in geo_dataframe.columns:
            return candidate
    # fallback: first non-geometry string column
    for column in geo_dataframe.columns:
        if column != geo_dataframe.geometry.name and geo_dataframe[column].dtype == object:
            return column
    raise ValueError("Couldn't detect a state-name column in the GeoDataFrame. Columns: " + ", ".join(geo_dataframe.columns))

def build_adjacency(geojson_path: str) -> Tuple[gpd.GeoDataFrame, Adjacency, str]:
    """
    Load geojson, fix geometries, create a deterministic adjacency list (touching or intersecting geometries).
    Returns (gdf, adjacency, state_name_column_used).
    """
    gdf = gpd.read_file(geojson_path)

    # make sure we work in a consistent CRS (WGS84 lat/lon)
    try:
        gdf = gdf.to_crs(epsg=4326)
    except Exception:
        # if conversion fails (already in 4326 or no crs), ignore
        pass

    state_name_column = detect_state_name_column(gdf)

    # ensure valid geometries (buffer(0) often repairs invalid polygons)
    gdf["geometry"] = gdf.geometry.buffer(0)

    # canonical state name column for keys
    gdf["state_name_for_csp"] = gdf[state_name_column].astype(str).str.strip()

    # spatial index for speed
    spatial_index = gdf.sindex

    adjacency: Adjacency = {}
    for row_index, row in gdf.iterrows():
        state_name = row["state_name_for_csp"]
        adjacency[state_name] = []

    # Build adjacency using bounding-box candidates and robust intersection tests
    for row_index, row in gdf.iterrows():
        state_name = row["state_name_for_csp"]
        geometry = row.geometry
        if geometry is None:
            continue
        candidate_indices = list(spatial_index.intersection(geometry.bounds))
        for candidate_index in candidate_indices:
            if candidate_index == row_index:
                continue
            candidate_state = gdf.at[candidate_index, "state_name_for_csp"]
            candidate_geometry = gdf.at[candidate_index, "geometry"]
            if candidate_geometry is None:
                continue
            are_neighbors = False
            try:
                # Prefer touches for clean boundary adjacency
                if geometry.touches(candidate_geometry):
                    are_neighbors = True
                else:
                    # fallback: check intersection non-empty (catches shared boundary lines and areas)
                    inter = geometry.intersection(candidate_geometry)
                    if inter is not None and not inter.is_empty:
                        are_neighbors = True
            except Exception:
                # Some geometries may cause topology errors; fallback to intersects
                try:
                    if geometry.intersects(candidate_geometry):
                        are_neighbors = True
                except Exception:
                    are_neighbors = False

            if are_neighbors:
                adjacency[state_name].append(candidate_state)

    # make adjacency lists deterministic and symmetric
    for state in list(adjacency.keys()):
        adjacency[state] = sorted(set(adjacency[state]))
    for state, neighbors in list(adjacency.items()):
        for neighbor in neighbors:
            if neighbor not in adjacency:
                continue
            if state not in adjacency[neighbor]:
                adjacency[neighbor].append(state)
                adjacency[neighbor] = sorted(set(adjacency[neighbor]))

    return gdf, adjacency, "state_name_for_csp"

# ----------------------------
# CSP components: variables/domains/constraint
# ----------------------------
def get_variables(adjacency: Adjacency) -> List[Variable]:
    """Return list of state names (variables) sorted deterministically."""
    return sorted(list(adjacency.keys()))

def get_domain(variable: Variable) -> List[Color]:
    """Return full palette as domain for each state (no precoloring)."""
    return list(COLOR_PALETTE)

def check_constraint(assignments: Dict[Variable, Color], adjacency: Adjacency, variable: Variable, color_choice: Color) -> bool:
    """
    Constraint: neighboring states must not have the same color.
    Check consistency of assigning `variable=color_choice` with current `assignments`.
    """
    for neighbor in adjacency.get(variable, []):
        if neighbor in assignments and assignments[neighbor] == color_choice:
            return False
    return True

# ----------------------------
# Selection (simple first-unassigned)
# ----------------------------
def select_unassigned_variable(variables: List[Variable], assignments: Dict[Variable, Color]) -> Optional[Variable]:
    """Return first variable (state) not yet assigned."""
    for variable in variables:
        if variable not in assignments:
            return variable
    return None

# ----------------------------
# Backtracking solver (simple)
# ----------------------------
assignments_count = 0
backtracks_count = 0

def backtrack_solve(variables: List[Variable], adjacency: Adjacency, assignments: Dict[Variable, Color], verbose: bool = True) -> Optional[Dict[Variable, Color]]:
    """
    Simple backtracking solver:
      - selects first unassigned variable
      - iterates its domain (full palette)
      - checks constraint against already assigned neighbors
      - assigns and recurses
    """
    global assignments_count, backtracks_count

    # completion check
    if len(assignments) == len(variables):
        return dict(assignments)

    variable = select_unassigned_variable(variables, assignments)
    if variable is None:
        return None

    domain_values = get_domain(variable)
    # deterministic ordering (sorted by color string)
    domain_values = sorted(domain_values)

    if verbose:
        print(f"Selecting variable: {variable}, domain = {domain_values}")

    for color_choice in domain_values:
        if not check_constraint(assignments, adjacency, variable, color_choice):
            if verbose:
                print(f"  => color {color_choice} not allowed for {variable} (neighbor conflict)")
            continue

        # assign
        assignments[variable] = color_choice
        assignments_count += 1
        if verbose:
            print(f"  ASSIGN {variable} = {color_choice}")

        result = backtrack_solve(variables, adjacency, assignments, verbose=verbose)
        if result is not None:
            return result

        # undo
        if verbose:
            print(f"  UNASSIGN {variable} (backtracking)")
        del assignments[variable]
        backtracks_count += 1

    return None

# ----------------------------
# Visualization helper (optional)
# ----------------------------
def plot_coloring(geo_dataframe: gpd.GeoDataFrame, state_name_column: str, solution: Dict[Variable, Color], out_png: str = "india_colored_simple.png"):
    gdf = geo_dataframe.copy()
    gdf[state_name_column] = gdf[state_name_column].astype(str).str.strip()
    gdf["fill_color"] = gdf[state_name_column].map(solution).fillna("#dddddd")
    fig, ax = plt.subplots(1, 1, figsize=(10, 12))
    gdf.plot(ax=ax, color=gdf["fill_color"], edgecolor="black", linewidth=0.4)
    ax.set_axis_off()
    plt.title("India states coloring (simple CSP solver)")
    plt.tight_layout()
    fig.savefig(out_png, dpi=200)
    print("Saved map to", out_png)
    plt.close(fig)

# ----------------------------
# Main (example)
# ----------------------------
if __name__ == "__main__":
    print("Loading GeoJSON:", GEOJSON_PATH)
    gdf, adjacency, state_name_column = build_adjacency(GEOJSON_PATH)
    variables = get_variables(adjacency)
    print(f"Detected {len(variables)} variables (states). Example variable: {variables[0] if variables else 'None'}")
    print("Sample adjacency (first 8 neighbors) for first variable:")
    if variables:
        print(" ", variables[0], "->", adjacency[variables[0]][:8])

    # print initial domains (showing first 12 variables for brevity)
    print("\nInitial domains (first 12 variables):")
    for state in variables[:12]:
        print(f"  {state}: {get_domain(state)}")

    # run simple solver
    assignments_count = 0
    backtracks_count = 0
    start_time = time.perf_counter()
    solution = backtrack_solve(variables, adjacency, {}, verbose=True)
    elapsed_time = time.perf_counter() - start_time

    if solution is None:
        print("\nNo solution found with palette of size", len(COLOR_PALETTE))
    else:
        print("\nSolution found!")
        for state in sorted(solution.keys()):
            print(f"{state}: {solution[state]}")

        # optional: save PNG
        try:
            plot_coloring(gdf, state_name_column, solution, out_png="india_colored_map.png")
        except Exception as plot_exc:
            print("Plotting failed:", plot_exc)

    print(f"\nAssignments: {assignments_count}, Backtracks: {backtracks_count}, Time: {elapsed_time:.4f}s")
