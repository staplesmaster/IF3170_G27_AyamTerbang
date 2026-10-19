"""Start a small Viser scene that can be viewed in a web browser."""

import signal
import time

import viser

from .view.control import Control
from .repository.parser import Parser
from .algorithm.steepest_ascent_hc import SteepestAscentHC
from .algorithm.sideways_move_hc import SidewaysMoveHC
from .algorithm.random_restart_hc import RandomRestartHC
from .algorithm.stochastic_hc import StochasticHC
from .algorithm.simulated_annealing import SimulatedAnnealing
from .models.objective_main import ObjectiveMain
from .models.objective_alt import ObjectiveAlt
from .models.simple_objective import SimpleObjective
from .algorithm.local_neighbor import RandomNeighbor


def main() -> None:
    # Untuk cleanup (CTRL+C) di container
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    server = viser.ViserServer()
    parser = Parser()
    objective = ObjectiveMain()
    algorithms = [SteepestAscentHC(objective),
                  SidewaysMoveHC(objective),
                  RandomRestartHC(objective),
                  StochasticHC(objective),
                  SimulatedAnnealing(objective)]

    control = Control(server, parser, algorithms)

    print("Server running")
    while True:
        time.sleep(10.0)



if __name__ == "__main__":
    main()
