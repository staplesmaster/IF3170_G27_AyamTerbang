from .local_search import Move, Neighborhood
from ..models.problem import Problem
from ..models.solution import Placement, State
from collections.abc import Iterable
from dataclasses import replace
import secrets

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
    new_placement: Placement | None
    def __init__(self, package_id: str, placement: Placement | None):
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
        1. Menukar dua paket (keduanya di dalam truk, atau satu di dalam dan satu di luar truk)
        2. Memindahkan sebuah paket ke suatu koordinat yang berbeda
        3. Merotasi paket di dalam truk 90° terhadap sumbu x, y, atau z
        """

        package_by_id = {package.id: package for package in problem.packages}
        packed = [
            ps
            for ps in state.package_states
            if ps.placement is not None and ps.package_id in package_by_id
        ]
        unpacked = [
            ps
            for ps in state.package_states
            if ps.placement is None and ps.package_id in package_by_id
        ]

        def placements(package_state):
            return [
                Placement(truck.id, (x, y, z))
                for truck in problem.trucks
                for x in range(truck.dimensions["w"])
                for y in range(truck.dimensions["l"])
                for z in range(truck.dimensions["h"])
            ]

        action_groups: list[list[Move]] = []

        swap_moves = [
            Swap(a.package_id, b.package_id)
            for i, a in enumerate(state.package_states)
            for b in state.package_states[i + 1 :]
            if a.placement is not None or b.placement is not None
        ]
        if swap_moves:
            action_groups.append(swap_moves)

        pack_moves = [
            ChangePlacement(ps.package_id, placement)
            for ps in unpacked
            for placement in placements(ps)
        ]
        if pack_moves:
            action_groups.append(pack_moves)

        unpack_moves = [ChangePlacement(ps.package_id, None) for ps in packed]
        if unpack_moves:
            action_groups.append(unpack_moves)

        translation_moves = [
            ChangePlacement(ps.package_id, placement)
            for ps in packed
            for placement in placements(ps)
            if placement != ps.placement
        ]
        if translation_moves:
            action_groups.append(translation_moves)

        rotate_moves = [
            Rotate(ps.package_id, orientation)
            for ps in packed
            for orientation in package_by_id[
                ps.package_id
            ].possible_orientations()
            if orientation != ps.orientation
        ]
        if rotate_moves:
            action_groups.append(rotate_moves)

        return [move for group in action_groups for move in group]
        

class RandomNeighbor(Neighborhood):
    neighbor_factory: LocalNeighbor
    def __init__(self):
        self.neighbor_factory = LocalNeighbor()

    def moves(self, problem: Problem, state: State) -> Iterable[Move]:
        """Return one random move from the full local neighborhood."""
        candidates = self.neighbor_factory.moves(problem, state)
        if not candidates:
            return ()
        return (secrets.choice(candidates),)
        
