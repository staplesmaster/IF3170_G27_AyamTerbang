from math import exp
from time import perf_counter

from ..models.objective import Objective
from ..models.problem import Problem
from ..models.solution import Result, State
from .base import AlgorithmOption
from .local_neighbor import RandomNeighbor
from .local_search import LocalSearchAlgorithm


class SimulatedAnnealing(LocalSearchAlgorithm):
    def __init__(self, objective: Objective) -> None:
        super().__init__(objective, RandomNeighbor())

    def getName(self) -> str:
        return "Simulated Annealing"

    def get_options(self) -> list[AlgorithmOption]:
        return [
            AlgorithmOption("initial_temp", "Initial temperature", "number", 100.0, minimum=0.000001),
            AlgorithmOption("threshold", "Temperature threshold", "number", 0.0001, minimum=0.000001),
            AlgorithmOption("decay", "Cooling rate", "slider", 0.9, minimum=0.8, maximum=0.99, step=0.01),
            AlgorithmOption("random_walk_threshold", "Random walk threshold", "slider", 0.5, minimum=0.0, maximum=1.0, step=0.01),
        ]

    def solve(self, problem: Problem, state: State, options: dict[str]) -> Result:
        start_time = perf_counter()
        initial_temp = float(options.get("initial_temp", 100.0))
        threshold = float(options.get("threshold", max(0.0001, initial_temp * 0.000001)))
        decay = float(options.get("decay", 0.9))
        random_walk_threshold = float(options.get("random_walk_threshold", 0.5))

        initial_state = state
        current_state = state
        current_value = self.objective.value(problem, current_state)

        history: list[float] = [current_value]
        random_walk_history: list[float] = []
        iterations = 0
        stuck_frequency = 0

        temp = initial_temp
        while temp > threshold:
            move = next(
                iter(self.neighborhood.moves(problem, current_state)), None
            )
            if move is None:
                break

            candidate_state = move.apply(current_state)
            candidate_value = self.objective.value(problem, candidate_state)
            delta_value = candidate_value - current_value

            iterations += 1

            if delta_value > 0:
                random_walk_probability = 1.0
                current_state = candidate_state
                current_value = candidate_value
            else:
                random_walk_probability = exp(delta_value / temp)
                if random_walk_probability > random_walk_threshold:
                    current_state = candidate_state
                    current_value = candidate_value
                else:
                    stuck_frequency += 1

            history.append(current_value)
            random_walk_history.append(random_walk_probability)

            temp *= decay

        duration = perf_counter() - start_time

        return Result(
            initial_state=initial_state,
            final_state=current_state,
            objective_value=current_value,
            objective_history=tuple(history),
            duration=duration,
            iterations=iterations,
            random_walk_history=tuple(random_walk_history),
            stuck_frequency=stuck_frequency,
        )