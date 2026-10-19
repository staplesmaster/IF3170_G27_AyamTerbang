from ..models.problem import Problem
from ..models.solution import State
from .local_neighbor import RandomNeighbor
from secrets import randbelow

class InitialStateFactory:
    neighbor_picker: RandomNeighbor

    def __init__(self):
        self.neighbor_picker = RandomNeighbor()

    def create(self, problem: Problem) -> State:
        state = State.from_problem(problem)
        iterations = 16 + randbelow(16)
        for _ in range(iterations):
            moves = self.neighbor_picker.moves(problem, state)
            move = next(iter(moves), None)
            if move is None:
                break
            state = move.apply(state)
        return state
