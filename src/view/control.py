import viser
from ..repository.parser import Parser
from .renderer import Renderer
from ..algorithm.base import Algorithm
from ..models.solution import *

class Control:

    server: viser.ViserServer
    parser: Parser
    renderer: Renderer
    algorithms: list[Algorithm]
    selected_algorithm: int

    uploadButton: viser.GuiUploadButtonHandle
    algorithmDropdown : viser.GuiDropdownHandle

    def __init__(self, server: viser.ViserServer, parser: Parser, algorithms: list[Algorithm]):
        self.server = server
        self.parser = parser
        self.algorithms = algorithms
        self.renderer = Renderer(server)

        self.uploadButton = self.server.gui.add_upload_button("Load config", hint="Upload file konfigurasi (JSON)")

        @self.uploadButton.on_upload
        def _(event: viser.GuiEvent) -> None:
            file = event.target.value
            # parse
            try:
                problem = self.parser.parse(file)
                initial_state = State.from_problem(problem)
                self.renderer.render(problem, initial_state)
            except RuntimeError:
                # nanti ganti error handlingnya
                print("error parsing file")

        self.algorithm_dropdown = server.gui.add_dropdown(
            "Algoritma Local Search",
            (algorithm.getName() for algorithm in self.algorithms)
        )

        @self.algorithm_dropdown.on_update
        def _(event: viser.GuiEvent) -> None:
            for i in range(len(self.algorithms)):
                if self.algorithms[i].getName() == event.target:
                    self.selected_algorithm = i
                    break


    