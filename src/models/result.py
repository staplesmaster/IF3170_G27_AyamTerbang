from dataclasses import dataclass

from .solution import State


@dataclass(frozen=True)
class Result:

    initial_state: State
    final_state: State  # State akhir pencarian.
    objective_value: float = 0.0

    # SA: nilai state per iterasi; GA: maksimum populasi per generasi.
    objective_history: tuple[float, ...] = ()
    # Khusus algoritma populasi seperti GA; algoritma lain dapat memakai ().
    mean_objective_history: tuple[float, ...] = ()

    duration: float = 0.0
    iterations: int = 0
    restarts: int = 0
    iterations_per_restart: tuple[int, ...] = ()
