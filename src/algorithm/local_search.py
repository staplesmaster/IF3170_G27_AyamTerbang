from abc import ABC, abstractmethod
from collections.abc import Iterable

from ..models.objective import Objective
from ..models.problem import Problem
from ..models.solution import State
from ..models.solution import Result
from .base import Algorithm


class Move(ABC):
    @abstractmethod
    def apply(self, state: State) -> State:
        raise NotImplementedError


class Neighborhood(ABC):
    @abstractmethod
    def moves(self, problem: Problem, state: State) -> Iterable[Move]:
        """Langkah neighbor (move) yang diperbolehkan tiap iterasi
        """
        raise NotImplementedError


class LocalSearchAlgorithm(Algorithm):
    objective: Objective
    neighborhood: Neighborhood

    def __init__(
        self,
        objective: Objective,
        neighborhood: Neighborhood
    ) -> None:
        self.objective = objective
        self.neighborhood = neighborhood

    @abstractmethod
    def solve(self, problem: Problem, state: State, options: dict[str]) -> Result:
        raise NotImplementedError