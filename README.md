# Setup

Install `pip install geopandas shapely matplotlib` only for map coloring.

---

## Constraint Satisfaction Problems (CSP)

- **Origins**: Rooted in mathematical logic & operations research.  
- **Adopted in AI**: 1960s–1970s as part of AI planning & problem-solving.  
- **Key Developments**:
  - Backtracking search formalized in AI.  
  - Constraint propagation & heuristics (1980s–1990s).  

**Significance**:  
- Became a general framework for solving many AI problems like scheduling, planning, and puzzles.

---

### Definition

A Constraint Satisfaction Problem is defined by:

- **Variables (X)**: Items to assign values.  
- **Domains (D)**: Possible values for each variable.  
- **Constraints (C)**: Rules restricting allowed combinations.  

**Goal**: Assign values to all variables such that *all constraints are satisfied*.

---

### Techniques

#### 1. Backtracking Search
- Assign a value → check constraints → backtrack if violated.

#### 2. Constraint Propagation
- Reduce domains by enforcing local consistency:
  - Forward checking
  - Arc-consistency (AC-3, etc.)

#### 3. Heuristics
- **MRV (Minimum Remaining Values)**: Choose the variable with the fewest remaining options.  
- **LCV (Least Constraining Value)**: Pick the value that rules out the fewest choices for other variables.  

#### 4. Optimization
- Combine backtracking + propagation + heuristics → much more efficient.

---

### Applications

- **Puzzles**: Sudoku, Crosswords, N-Queens.  
- **Scheduling**: Exam timetables, employee rosters.  
- **Resource Allocation**: Assigning tasks to machines, CPU scheduling.  
- **Map Colouring**: Colour regions so that no two adjacent areas share the same colour.  
- **AI Planning**: Robotics, automated configuration, plan generation.  

---
