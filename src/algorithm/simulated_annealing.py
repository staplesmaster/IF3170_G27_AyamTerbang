from ..models.problem import Problem
from ..models.solution import State
from .base import AlgorithmOption
from .local_search import LocalSearchAlgorithm
from .local_neighbor import RandomNeighbor
from math import exp

class SimulatedAnnealing(LocalSearchAlgorithm):
    def __init__(self, objective):
        super().__init__(objective, RandomNeighbor())

    def getName(self):
        return "Simulated Annealing"

    def get_options(self) -> list[AlgorithmOption]:
        return [
            AlgorithmOption("initial_temp", "Initial temperature", "number", 100.0, minimum=0.000001),
            AlgorithmOption("threshold", "Temperature threshold", "number", 0.0001, minimum=0.000001),
            AlgorithmOption("decay", "Cooling rate", "slider", 0.9, minimum=0.8, maximum=0.99, step=0.01),
            AlgorithmOption("random_walk_threshold", "Random walk threshold", "slider", 0.5, minimum=0.0, maximum=1.0, step=0.01),
        ]

    def solve(self, problem: Problem, state: State, options: dict[str]) -> State:
        initial_temp = float(options.get("initial_temp", 100.0))
        threshold = float(options.get("threshold", max(0.0001, initial_temp * 0.000001)))
        decay = float(options.get("decay", 0.9))
        random_walk_threshold = float(options.get("random_walk_threshold", 0.5))

        temp = initial_temp
        current_value = self.objective.value(problem, state)
        while temp > threshold:
            move = next(iter(self.neighborhood.moves(problem, state)), None)
            if move is None:
                break

            candidate_state = move.apply(state)
            candidate_value = self.objective.value(problem, candidate_state)
            delta_value = candidate_value - current_value

            if delta_value > 0:
                state = candidate_state
                current_value = candidate_value
            else:
                random_walk_probability = exp(delta_value / temp)
                if random_walk_probability > random_walk_threshold:
                    state = candidate_state
                    current_value = candidate_value

            temp *= decay

        return state
