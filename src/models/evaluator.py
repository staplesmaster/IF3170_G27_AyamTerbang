from dataclasses import dataclass

from .objective import Objective
from .problem import Problem
from .solution import Solution
from .validator import PackingValidator


@dataclass(frozen=True)
class Evaluation:
    feasible: bool
    value: float


class Evaluator:
    def __init__(self, objective: Objective, validator: PackingValidator) -> None:
        self.objective = objective
        self.validator = validator

    def evaluate(self, problem: Problem, solution: Solution) -> Evaluation:
        feasible = self.validator.validate(problem, solution)
        value = self.objective.value(problem, solution) if feasible else float("-inf")
        return Evaluation(feasible, value)