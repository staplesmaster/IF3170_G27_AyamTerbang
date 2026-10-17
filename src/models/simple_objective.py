from .objective import Objective
from .problem import Problem
from .solution import State

class SimpleObjective(Objective):
    def value(self, problem: Problem, state: State) -> float:
        packages_by_id = {package.id: package for package in problem.packages}
        return float(
            sum(
                packages_by_id[package_state.package_id].value
                for package_state in state.package_states
                if package_state.placement is not None
            )
        )