from time import perf_counter

from ..models.objective import Objective
from ..models.problem import Problem
from ..models.solution import Result, State
from .local_neighbor import LocalNeighbor
from .local_search import LocalSearchAlgorithm


class SteepestAscentHC(LocalSearchAlgorithm):
    def __init__(self, objective: Objective) -> None:
        super().__init__(objective, LocalNeighbor())

    def getName(self) -> str:
        return "Steepest Ascent Hill Climbing"

    def solve(self, problem: Problem, state: State, options: dict[str]) -> Result:
        start_time = perf_counter()

        initial_state = state
        current_state = state
        current_value = self.objective.value(problem, current_state)
        history: list[float] = [current_value]
        iterations = 0

        while True:
            best_neighbor_state: State | None = None
            best_neighbor_value = current_value

            for move in self.neighborhood.moves(problem, current_state):
                candidate_state = move.apply(current_state)
                candidate_value = self.objective.value(problem, candidate_state)

                if candidate_value > best_neighbor_value:
                    best_neighbor_value = candidate_value
                    best_neighbor_state = candidate_state

            if best_neighbor_state is None:
                break

            current_state = best_neighbor_state
            current_value = best_neighbor_value
            iterations += 1
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