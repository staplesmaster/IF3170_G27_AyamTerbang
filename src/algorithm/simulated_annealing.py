from ..models.problem import Problem
from ..models.solution import State
from .base import AlgorithmOption
from .local_search import LocalSearchAlgorithm

class SimulatedAnnealing(LocalSearchAlgorithm):
    def getName(self):
        return "Simulated Annealing"

    def get_options(self) -> list[AlgorithmOption]:
        return [
            AlgorithmOption("initial_temp", "Initial temperature", "number", 100.0, minimum=0.000001),
            AlgorithmOption("threshold", "Temperature threshold", "number", 0.0001, minimum=0.000001),
            AlgorithmOption("decay", "Cooling rate", "slider", 0.9, minimum=0.8, maximum=0.99, step=0.01),
        ]

    def solve(self, problem: Problem, options: dict[str]) -> State:
        initial_temp = float(options.get("initial_temp", 100.0))
        threshold = float(options.get("threshold", max(0.0001, initial_temp * 0.000001)))
        decay = float(options.get("decay", 0.9))

        return State.from_problem(problem)
