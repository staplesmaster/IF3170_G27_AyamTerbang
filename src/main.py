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
        for h in truckHandles:
            h.remove()

        truckHandles.clear()

        for h in packageHandles.values():
            h.remove()

        packageHandles.clear()

        # visualize
        gap = 2.0
        wallThickness = 0.2
        totalWidth = sum(t.dimensions["w"] for t in problem.trucks)
        totalWidth += gap * max(len(problem.trucks) - 1, 0)
        truckX = -totalWidth / 2

        for t in problem.trucks:
            width = t.dimensions["w"]
            truckLength = t.dimensions["l"]
            truckHeight = t.dimensions["h"]
            centerX = truckX + width / 2
            centerY = truckLength / 2
            wallCenterZ = truckHeight / 2 + wallThickness

            truckHandles.extend((
                server.scene.add_box(
                    name=f"{t.id}/base",
                    position=(centerX, centerY, wallThickness / 2),
                    dimensions=(width, truckLength, wallThickness),
                ),
                server.scene.add_box(
                    name=f"{t.id}/left",
                    position=(centerX - width / 2, centerY, wallCenterZ),
                    dimensions=(wallThickness, truckLength, truckHeight),
                ),
                server.scene.add_box(
                    name=f"{t.id}/right",
                    position=(centerX + width / 2, centerY, wallCenterZ),
                    dimensions=(wallThickness, truckLength, truckHeight),
                ),
                server.scene.add_box(
                    name=f"{t.id}/front",
                    position=(centerX, centerY + truckLength / 2, wallCenterZ),
                    dimensions=(width, wallThickness, truckHeight),
                ),
            ))
            truckX += width + gap
    
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
