from .local_search import Move, Neighborhood
from ..models.problem import Problem
from ..models.solution import Placement, State
from collections.abc import Iterable
from dataclasses import replace

class Swap(Move):
    package_a_id: str
    package_b_id: str
    def __init__(self, package_a_id: str, package_b_id: str):
        self.package_a_id = package_a_id
        self.package_b_id = package_b_id

    def apply(self, state: State) -> State:
        states_list = list(state.package_states)

        a_index = -1
        b_index = -1
        for i in range(len(state.package_states)):
            if state.package_states[i].package_id == self.package_a_id:
                a_index = i
            elif state.package_states[i].package_id == self.package_b_id:
                b_index = i
            if a_index != -1 and b_index != -1:
                break

        placement_a = states_list[a_index].placement
        placement_b = states_list[b_index].placement

        states_list[a_index] = replace(states_list[a_index], placement=placement_b)
        states_list[b_index] = replace(states_list[b_index], placement=placement_a)

        return replace(state, package_states=tuple(states_list))
        
class ChangePlacement(Move):
    """Untuk Pack, Unpack, sama pindah koordinat/truck"""
    package_id: str
    new_placement: Placement
    def __init__(self, package_id: str, placement: Placement):
        self.package_id = package_id
        self.new_placement = placement

    def apply(self, state: State) -> State:
        states_list = list(state.package_states)
        index = -1
        for i in range(len(state.package_states)):
            if state.package_states[i].package_id == self.package_id:
                index = i
                break
        states_list[index] = replace(states_list[index], placement=self.new_placement)
        return replace(state, package_states=tuple(states_list))

class Rotate(Move):
    package_id: str
    new_orientation: tuple[str, str, str]
    def __init__(self, package_id: str, orientation: tuple[str, str, str]):
        self.package_id = package_id
        self.new_orientation = orientation

    def apply(self, state: State) -> State:
        states_list = list(state.package_states)
        index = -1
        for i in range(len(state.package_states)):
            if state.package_states[i].package_id == self.package_id:
                index = i
                break
        states_list[index] = replace(states_list[index], orientation=self.new_orientation)
        return replace(state, package_states=tuple(states_list))

class LocalNeighbor(Neighborhood):

    def moves(self, problem: Problem, state: State) -> Iterable[Move]:
        """Langkah neighbor (move) yang diperbolehkan tiap iterasi:
        1. Menukar dua paket, baik di dalam maupun di luar truk
        2. Memindahkan sebuah paket ke suatu koordinat yang berbeda
        3. Merotasi paket 90° terhadap sumbu x, y, atau z
        """

        move_list = list[Move]()

        for packed_id in state.placed_package_ids:
            for package in state.package_states:
                if package.package_id != packed_id:
                    move_list.append(Swap(packed_id, package.package_id))
        
        # nanti tambahin yang langkah 2 sama 3
        

class RandomNeighbor(Neighborhood):
    def moves(self, problem: Problem, state: State) -> Iterable[Move]:
        """hanya menghasilkan 1 neighbor random"""