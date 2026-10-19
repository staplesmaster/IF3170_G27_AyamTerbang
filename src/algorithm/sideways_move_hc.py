from time import perf_counter

from .base import AlgorithmOption
from ..models.objective import Objective
from ..models.problem import Problem
from ..models.solution import Result, State
from .local_neighbor import LocalNeighbor
from .local_search import LocalSearchAlgorithm


class SidewaysMoveHillClimbing(LocalSearchAlgorithm):
    def __init__(self, objective: Objective) -> None:
        super().__init__(objective, LocalNeighbor())

    def getName(self) -> str:
        return "Sideways Move Hill Climbing"

    def get_options(self) -> list[AlgorithmOption]:
        return [
            AlgorithmOption("max_sideways_moves","Maximum consecutive sideways moves", "number", 20, minimum=0, step=1),
        ]

    def solve(self, problem: Problem, state: State, options: dict[str]) -> Result:
        start_time = perf_counter()

        max_sideways_moves = max(0, int(options.get("max_sideways_moves", 20)))

        initial_state = state
        current_state = state
        current_value = self.objective.value(problem, current_state)
        history: list[float] = [current_value]
        iterations = 0
        sideways_moves = 0

        while True:
            best_neighbor_state: State | None = None
            best_neighbor_value = current_value

            for move in self.neighborhood.moves(problem, current_state):
                candidate_state = move.apply(current_state)
                candidate_value = self.objective.value(problem, candidate_state)

                if candidate_value >= best_neighbor_value:
                    best_neighbor_value = candidate_value
                    best_neighbor_state = candidate_state

            if best_neighbor_state is None:
                break

            if best_neighbor_value == current_value:
                if sideways_moves >= max_sideways_moves:
                    break

                sideways_moves += 1
            else:
                sideways_moves = 0

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