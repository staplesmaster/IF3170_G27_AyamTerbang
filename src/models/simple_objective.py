from .objective import Objective
from .problem import Problem
from .solution import Solution

class SimpleObjective(Objective):
    def value(self, problem: Problem, solution: Solution) -> float:
        packages_by_id = {package.id: package for package in problem.packages}
        return float(
            sum(packages_by_id[placement.package_id].value for placement in solution.placements)
        )