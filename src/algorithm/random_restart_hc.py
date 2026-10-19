from time import perf_counter

from algorithm.initial_state_factory import InitialStateFactory
from .base import AlgorithmOption
from ..models.objective import Objective
from ..models.problem import Problem
from ..models.solution import Result, State
from .local_neighbor import LocalNeighbor
from .local_search import LocalSearchAlgorithm


class RandomRestartHC(LocalSearchAlgorithm):
    def __init__(self, objective: Objective) -> None:
        super().__init__(objective, LocalNeighbor())
        self.initial_state_factory = InitialStateFactory()

    def getName(self) -> str:
        return "Random Restart Hill Climbing"

    def get_options(self) -> list[AlgorithmOption]:
        return [
            AlgorithmOption("max_restart", "Maximum restarts", "number", 10, minimum=0, step=1, ),
        ]

    def solve(self, problem: Problem, state: State, options: dict[str]) -> Result:
        start_time = perf_counter()

        max_restart = max(0, int(options.get("max_restart", 10)))

       
        session_initial_state = state
        current_state = state
        current_value = self.objective.value(problem, current_state)

        history: list[float] = [current_value]

        iterations = 0
        restarts = 0
        iterations_per_restart: list[int] = []

        best_initial_state = current_state
        best_final_state = current_state
        best_value = current_value

        while True:
            session_iterations = 0

            while True:
                best_neighbor_state: State | None = None
                best_neighbor_value = current_value

                for move in self.neighborhood.moves(
                    problem, current_state
                ):
                    candidate_state = move.apply(current_state)
                    candidate_value = self.objective.value(
                        problem, candidate_state
                    )

                    if candidate_value > best_neighbor_value:
                        best_neighbor_value = candidate_value
                        best_neighbor_state = candidate_state

                if best_neighbor_state is None:
                    break

                current_state = best_neighbor_state
                current_value = best_neighbor_value

                session_iterations += 1
                iterations += 1
                history.append(current_value)

            iterations_per_restart.append(session_iterations)

            if current_value > best_value:
                best_initial_state = session_initial_state
                best_final_state = current_state
                best_value = current_value

            if restarts >= max_restart:
                break

            session_initial_state = (self.initial_state_factory.create(problem))
            current_state = session_initial_state
            current_value = self.objective.value(problem, current_state)

            history.append(current_value)

            restarts += 1

        duration = perf_counter() - start_time

        return Result(
            initial_state=best_initial_state,
            final_state=best_final_state,
            objective_value=best_value,
            objective_history=tuple(history),
            duration=duration,
            iterations=iterations,
            restarts=restarts,
            iterations_per_restart=tuple(iterations_per_restart),
        )