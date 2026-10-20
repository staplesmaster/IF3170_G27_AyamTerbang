"""Start a small Viser scene that can be viewed in a web browser."""

import signal
import time

import viser

from .view.control import Control
from .repository.parser import Parser
from .algorithm.simulated_annealing import SimulatedAnnealing
from .algorithm.genetic_algorithm import GeneticAlgorithm
from .models.objective_main import ObjectiveMain
from .models.simple_objective import SimpleObjective


def main() -> None:
    # Untuk cleanup (CTRL+C) di container
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    server = viser.ViserServer()
    parser = Parser()
    objective = SimpleObjective()
    algorithms = [SimulatedAnnealing(objective), GeneticAlgorithm(ObjectiveMain())]

    control = Control(server, parser, algorithms)

    print("Server running")
    while True:
        time.sleep(10.0)



if __name__ == "__main__":
    main()
