from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..models.evaluator import Evaluator
from ..models.problem import Problem
from ..models.solution import State
from .base import Algorithm


class Move(ABC):
    @abstractmethod
    def apply(self, solution: State) -> State:
        raise NotImplementedError


class Neighborhood(ABC):
    @abstractmethod
    def moves(self, problem: Problem, solution: State) -> Iterable[Move]:
        raise NotImplementedError


class InitialStateFactory(ABC):
    @abstractmethod
    def create(self, problem: Problem) -> State:
        raise NotImplementedError


class LocalSearchAlgorithm(Algorithm):
    def __init__(
        self,
        evaluator: Evaluator,
        neighborhood: Neighborhood,
        initial_solutions: InitialStateFactory,
    ) -> None:
        self.evaluator = evaluator
        self.neighborhood = neighborhood
        self.initial_solutions = initial_solutions

    @abstractmethod
    def solve(self, problem: Problem) -> State:
        raise NotImplementedError