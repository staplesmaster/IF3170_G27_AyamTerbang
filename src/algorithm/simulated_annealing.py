from ..models.problem import Problem
from ..models.solution import State
from .base import Algorithm

class SimulatedAnnealing(Algorithm):
    def getName(self):
        return "Simulated Annealing"

    def solve(self, problem: Problem) -> State:
        return State.from_problem(problem)