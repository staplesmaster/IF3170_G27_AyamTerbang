"""Start a small Viser scene that can be viewed in a web browser."""

import signal
import time

import viser

from .view.control import Control
from .repository.parser import Parser
from .algorithm.simulated_annealing import SimulatedAnnealing


def main() -> None:
    # Untuk cleanup (CTRL+C) di container
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    server = viser.ViserServer()
    parser = Parser()
    algorithms = [SimulatedAnnealing()]

    control = Control(server, parser, algorithms)

    print("Server running")
    while True:
        time.sleep(10.0)



if __name__ == "__main__":
    main()
