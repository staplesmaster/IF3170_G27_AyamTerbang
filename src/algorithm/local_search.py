from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..models.evaluator import Evaluator
from ..models.problem import Problem
from ..models.solution import Solution
from .base import Algorithm


class Move(ABC):
    @abstractmethod
    def apply(self, solution: Solution) -> Solution:
        raise NotImplementedError


class Neighborhood(ABC):
    @abstractmethod
    def moves(self, problem: Problem, solution: Solution) -> Iterable[Move]:
        raise NotImplementedError


class InitialSolutionFactory(ABC):
    @abstractmethod
    def create(self, problem: Problem) -> Solution:
        raise NotImplementedError


class LocalSearchAlgorithm(Algorithm):
    def __init__(
        self,
        evaluator: Evaluator,
        neighborhood: Neighborhood,
        initial_solutions: InitialSolutionFactory,
    ) -> None:
        self.evaluator = evaluator
        self.neighborhood = neighborhood
        self.initial_solutions = initial_solutions

    @abstractmethod
    def solve(self, problem: Problem) -> Solution:
        raise NotImplementedError