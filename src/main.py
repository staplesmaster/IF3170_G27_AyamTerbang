"""Start a small Viser scene that can be viewed in a web browser."""

import signal
import time

import viser

from .repository.parser import Parser


def main() -> None:
    # Untuk cleanup (CTRL+C) di container
    signal.signal(signal.SIGTERM, signal.default_int_handler)

    # Contoh implementai https://viser.studio/main/examples/getting_started/core_concepts/
    server = viser.ViserServer()
    parser = Parser()

    truckHandles = []
    packageHandles = {}

    # Create GUI controls
    load_config = server.gui.add_upload_button("Load config", hint="Upload file konfigurasi (JSON)")

    @load_config.on_upload
    def _(event: viser.GuiEvent) -> None:
        file = event.target.value
        # parse
        problem = parser.parse(file)
    
    algorithm_dropdown = server.gui.add_dropdown(
        "Algoritma Local Search",
        (
            "Steepest Ascent Hill-Climbing",
            "Hill-Climbing with Sideways Move",
            "Random Restart Hill-Climbing",
            "Stochastic Hill-Climbing",
            "Simulated Annealing",
            "Genetic Algorithm"
        )
    )

    print("Server running")
    while True:
        time.sleep(10.0)



if __name__ == "__main__":
    main()
