from time import perf_counter

from .base import AlgorithmOption
from ..models.objective import Objective
from ..models.problem import Problem
from ..models.solution import Result, State
from .local_neighbor import RandomNeighbor
from .local_search import LocalSearchAlgorithm


class StochasticHillClimbing(LocalSearchAlgorithm):
    def __init__(self, objective: Objective) -> None:
        super().__init__(objective, RandomNeighbor())

    def getName(self) -> str:
        return "Stochastic Hill Climbing"

    def get_options(self) -> list[AlgorithmOption]:
        return [
            AlgorithmOption("max_random_attempts", "Maximum consecutive random attempts without improvement", "number", 100, minimum=1, step=1),
        ]

    def solve(self, problem: Problem, state: State, options: dict[str]) -> Result:
        start_time = perf_counter()

        max_random_attempts = max(1, int(options.get("max_random_attempts", 100)))

        initial_state = state
        current_state = state
        current_value = self.objective.value(problem, current_state)

        history: list[float] = [current_value]
        iterations = 0
        consecutive_failures = 0

        while consecutive_failures < max_random_attempts:
            candidate_state = self.neighborhood.moves(problem, current_state)

            if candidate_state is None:
                break

            candidate_value = self.objective.value(
                problem, candidate_state
            )

            iterations += 1

            if candidate_value > current_value:
                current_state = candidate_state
                current_value = candidate_value

                consecutive_failures = 0
            else:
                consecutive_failures += 1

            history.append(current_value)

        duration = perf_counter() - start_time

        return Result(
            initial_state=initial_state,
            final_state=current_state,
            objective_value=current_value,
            objective_history=tuple(history),
            duration=duration,
            iterations=iterations,
        )