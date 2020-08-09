import random
from ortools.sat.python import cp_model


class Binairo:
    """
    Binairo game grid

    Arguments:
        size: Size of the grid
        initial_grid: Give a specific grid, otherwise it will be randomly generated
    """

    def __init__(self, size, initial_grid=None):
        self.size = size

        # Build game grid
        if initial_grid is None:
            # Random grid
            self.grid = self._generate_random_grid()
        else:
            # Retrieve given grid
            self.grid = initial_grid

        # Track squares whose value has been assigned
        self.filled_squares = [(x, y) for x in range(size)
                               for y in range(size)]

        # Saver variable to cancel last remove
        self.last_removed = None

    def _generate_random_grid(self):
        'Init binairo grid (2D array) with random 0 and 1'
        return [[random.randint(0, 1)] *
                self.size for _ in range(self.size)]

    def remove_random_square(self):
        'Remove a square in grid at random'
        # Select random square which is not already set to None
        assert len(self.filled_squares) > 0
        square_idx = random.randint(0, len(self.filled_squares)-1)
        i, j = self.filled_squares[square_idx]
        value = self.grid[i][j]

        # Set it to None
        self.grid[i][j] = None

        # Remove square from filled square
        self.filled_squares.pop(square_idx)
        self.last_removed = (i, j, value)

    def cancel_last_remove(self):
        'Cancel last removed square'
        i, j, value = self.last_removed
        self.grid[i][j] = value
        self.filled_squares.append((i, j))

    def __str__(self):
        'Generate string representation of binairo grid'
        string = ""
        newline = "\n"+"_"*(self.size*2+1)+"\n"
        string += newline

        for i in range(self.size):
            string += "|"
            for j in range(self.size):
                value = self.grid[i][j]
                string += str(value) if value is not None else " "
                string += "|"
            string += newline
        return string


class BinairoGenerator:
    """
    Generate random solvable binairo grid using constraint solver

    Game rules / constraints:
         C1: no three consecutive elements in rows or columns <=> 0 < sum(three consecutive elements) < 3
         C2: Each lign and each column contains as many 0 as 1 <=> rows and columns sum to half the size
         C3: 2 ligns / columns cannot be the same 
    """

    def __init__(self, board_size=6):
        self.board_size = board_size

    def _build_var_grid(self):
        'Build grid of int variables to ease the access'
        self.var_grid = {}
        for i in range(self.board_size):
            for j in range(self.board_size):
                self.var_grid[(i, j)] = self.model.NewIntVar(
                    0, 1, str((i, j)))

    def _add_initial_values(self):
        'Add constraint for variables already placed in grid (value not None)'
        for i in range(self.board_size):
            for j in range(self.board_size):
                if self.binairo.grid[i][j] is not None:
                    self.model.Add(
                        self.var_grid[(i, j)] == self.binairo.grid[i][j])

    def _add_constraint_c1(self):
        'Add constraint C1: no same three consecutive elements in rows or columns'
        for i in range(self.board_size):
            for j in range(self.board_size - 2):
                # Rows
                sum_three_consecutives_row = sum(
                    [self.var_grid[(i, jl)] for jl in range(self.board_size)[j:j + 3]])

                self.model.Add(sum_three_consecutives_row > 0)
                self.model.Add(sum_three_consecutives_row < 3)

                # Columns
                sum_three_consecutives_col = sum(
                    [self.var_grid[(jl, i)] for jl in range(self.board_size)[j:j + 3]])

                self.model.Add(sum_three_consecutives_col > 0)
                self.model.Add(sum_three_consecutives_col < 3)

    def _add_constraint_c2(self):
        'Add constraint C2: rows and columns sum to half the size'
        line_sum = self.board_size // 2
        # Rows
        for i in range(self.board_size):
            row_sum = sum([self.var_grid[(i, j)]
                           for j in range(self.board_size)])
            self.model.Add(row_sum == line_sum)

        # Columns
        for j in range(self.board_size):
            col_sum = sum([self.var_grid[(i, j)]
                           for i in range(self.board_size)])
            self.model.Add(col_sum == line_sum)

    def _is_valid_c3(self, board):
        """
        Checks whether a board has no duplicate rows or columns according to C3: 2 ligns / columns cannot be the same.
        This function is needed to filter out invalid solutions from the constraint solver.
        """
        # Set is used here to remove duplicates and to check is its len is the same as list with potential duplicates
        return ((len(set(map(tuple, board))) == len(board)) and
                (len(set(zip(*board))) == len(board)))

    def _solve(self):
        'Get problem solutions using solver'
        solver = cp_model.CpSolver()

        # Solver options: TODO: see if it is usefull to change
        # solver.parameters.linearization_level = 0
        # solver.parameters.max_time_in_seconds = 1.0

        solution_printer = VarArraySolutions(
            variables=self.var_grid, max_solutions_until_stop=2)
        result = solver.SearchForAllSolutions(self.model, solution_printer)

        # Parse solutions from solver and get clean solution
        raw_solutions = solution_printer.solutions()
        clean_solutions = []
        if result == cp_model.FEASIBLE or result == cp_model.OPTIMAL:
            clean_solutions = [[[raw_solutions[s][i+j] for i in range(
                self.board_size)] for j in range(self.board_size)] for s in range(len(raw_solutions))]

        return clean_solutions

    def _get_valid_solutions(self):
        'Sort solutions in order to exclude non valid solutions according to C3'
        self.model = cp_model.CpModel()
        self._build_var_grid()
        self._add_initial_values()
        self._add_constraint_c1()
        self._add_constraint_c2()
        solutions_without_c3 = self._solve()

        # (C3) search for all solutions and remove those with duplicate rows or columns
        iterator_solutions = filter(self._is_valid_c3, solutions_without_c3)
        solutions = [solution for solution in iterator_solutions]
        return solutions

    def generate_binairo(self):
        """
        Generate a solvable binairo and give the solution

        Return: Tuple(generated binairo, solution)   
        """
        self.binairo = Binairo(self.board_size)
        solutions = self._get_valid_solutions()

        while len(solutions) == 0:
            last_solutions = solutions
            self.binairo.remove_random_square()
            solutions = self._get_valid_solutions()

            # If multiple solutions, we removed a bad square so cancel last remove!
            if len(solutions) > 1:
                self.binairo.cancel_last_remove()
                solutions = last_solutions

        return self.binairo, solutions[0]


class VarArraySolutions(cp_model.CpSolverSolutionCallback):
    """
    Get solutions

    Arguments:
        variables: Model variables dict whose keys are var names and dict values their values
        max_solutions_until_stop: Stop search after this number of solutions is reached
    """

    def __init__(self, variables, max_solutions_until_stop):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._variables = variables.values()
        self.max_solutions_until_stop = max_solutions_until_stop
        self._solution_count = 0
        self._solutions = []

    def on_solution_callback(self):
        self._solution_count += 1
        solution = []
        for v in self._variables:
            solution.append(self.Value(v))

        self._solutions.append(solution)
        if self._solution_count >= 2:
            self.StopSearch()

    def solutions(self):
        return self._solutions


if __name__ == "__main__":
    generator = BinairoGenerator(board_size=6)

    binairo, solution = generator.generate_binairo()
    print("Generated binairo:")
    print(binairo)

    solution = Binairo(size=6, initial_grid=solution)
    print("Solution:")
    print(solution)
