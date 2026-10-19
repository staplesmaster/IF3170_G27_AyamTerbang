from dataclasses import dataclass


@dataclass(frozen=True)
class Placement:
    truck_id: str
    position: tuple[int, int, int]


@dataclass(frozen=True)
class PackageState:
    package_id: str
    orientation: tuple[str, str, str]
    placement: Placement | None = None


@dataclass(frozen=True)
class State:
    package_states: tuple[PackageState, ...] = ()

    @classmethod
    def from_problem(cls, problem) -> "State":
        return cls(
            tuple(
                PackageState(
                    package_id=package.id,
                    orientation=package.initial_orientation,
                )
                for package in problem.packages
            )
        )

    @property
    def placed_package_ids(self) -> frozenset[str]:
        return frozenset(
            package_state.package_id
            for package_state in self.package_states
            if package_state.placement is not None
        )

@dataclass(frozen=True)
class Result:
    initial_state: State                              # State awal
    final_state: State                                # State akhir
    objective_value: float = 0.0                      # Nilai objective akhir
    objective_history: tuple[float, ...] = ()         # Nilai objective tiap iterasi
    duration: float = 0.0                             # Durasi pencarian (detik)
    iterations: int = 0                               # Banyak iterasi yang dilakukan
    restarts: int = 0                                 # Khusus Random Restart: banyak restart
    iterations_per_restart: tuple[int, ...] = ()      # Khusus Random Restart: iterasi tiap restart