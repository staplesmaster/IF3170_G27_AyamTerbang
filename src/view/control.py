import io
import numpy as np
import viser
from ..repository.parser import Parser
from .renderer import Renderer
from ..algorithm.base import Algorithm, AlgorithmOption
from ..models.problem import Problem
from ..models.solution import Result, State
from ..algorithm.initial_state_factory import InitialStateFactory


class Control:

    server: viser.ViserServer
    parser: Parser
    renderer: Renderer
    algorithms: list[Algorithm]
    selected_algorithm: int
    problem: Problem | None
    state: State | None
    result: Result | None
    option_handles: dict[str, object]

    uploadButton: viser.GuiUploadButtonHandle
    algorithmDropdown: viser.GuiDropdownHandle
    solveButton: viser.GuiButtonHandle
    statusMarkdown: viser.GuiMarkdownHandle
    stateViewDropdown: viser.GuiDropdownHandle | None
    statsFolder: viser.GuiFolderHandle | None
    plotsFolder: viser.GuiFolderHandle | None
    initialStateFactory: InitialStateFactory

    def __init__(
        self,
        server: viser.ViserServer,
        parser: Parser,
        algorithms: list[Algorithm],
    ):
        self.server = server
        self.parser = parser
        self.algorithms = algorithms
        self.renderer = Renderer(server)
        self.selected_algorithm = 0
        self.problem = None
        self.state = None
        self.result = None
        self.option_handles = {}
        self.stateViewDropdown = None
        self.statsFolder = None
        self.plotsFolder = None
        self.initialStateFactory = InitialStateFactory()

        self.uploadButton = self.server.gui.add_upload_button(
            "Load config", hint="Upload file konfigurasi (JSON)"
        )

        self.statusMarkdown = self.server.gui.add_markdown(
            "ℹ️ **Status:** Silakan unggah file konfigurasi JSON."
        )

        @self.uploadButton.on_upload
        def _(event: viser.GuiEvent) -> None:
            file = event.target.value
            try:
                self.statusMarkdown.content = (
                    "⏳ **Status:** Memuat konfigurasi dan membuat Initial State..."
                )
                problem = self.parser.parse(file)
                self.problem = problem
                initial_state = self.initialStateFactory.create(problem)
                self.state = initial_state
                self.result = None
                self._clear_result_cards()
                self.renderer.render(problem, initial_state)
                self.solveButton.disabled = False
                self.statusMarkdown.content = (
                    f"✅ **Status:** Konfigurasi dimuat ({len(problem.packages)} paket, "
                    f"{len(problem.trucks)} truk). Siap menjalankan **Solve**."
                )
            except RuntimeError:
                self.statusMarkdown.content = (
                    "❌ **Status:** Gagal membaca file konfigurasi JSON."
                )
                print("error parsing file")

        self.algorithm_dropdown = server.gui.add_dropdown(
            "Algoritma Local Search",
            tuple(algorithm.getName() for algorithm in self.algorithms),
        )

        if self.algorithms:
            self._show_algorithm_options(self.algorithms[0].get_options())

        self.solveButton = server.gui.add_button("Solve", disabled=True)

        @self.solveButton.on_click
        def _(_: viser.GuiEvent) -> None:
            if self.problem is None or self.state is None or not self.algorithms:
                return

            algorithm = self.algorithms[self.selected_algorithm]
            options = {
                key: handle.value for key, handle in self.option_handles.items()
            }

            # Tampilkan status loading selama algoritma bekerja
            self.solveButton.disabled = True
            self.statusMarkdown.content = (
                f"⏳ **Status:** Sedang menjalankan **{algorithm.getName()}**... "
                "Mohon tunggu."
            )

            output = algorithm.solve(self.problem, self.state, options=options)

            if isinstance(output, Result):
                self.result = output
            else:
                self.result = Result(
                    initial_state=self.state,
                    final_state=output,
                )

            self.renderer.render(self.problem, self.result)
            self._show_state_view_selector()
            self._show_stats_card(algorithm.getName(), self.result)
            self._show_plots_card(algorithm.getName(), self.result)

            self.statusMarkdown.content = (
                f"✅ **Status:** Pencarian **{algorithm.getName()}** selesai "
                f"dalam `{self.result.duration:.4f}` detik."
            )
            self.solveButton.disabled = False

        @self.algorithm_dropdown.on_update
        def _(event: viser.GuiEvent) -> None:
            selected_name = event.target.value
            for i, algorithm in enumerate(self.algorithms):
                if algorithm.getName() == selected_name:
                    self.selected_algorithm = i
                    self._show_algorithm_options(algorithm.get_options())
                    if self.problem is not None and self.state is not None:
                        self.solveButton.disabled = False
                    break

    def _clear_result_cards(self) -> None:
        if self.stateViewDropdown is not None:
            self.stateViewDropdown.remove()
            self.stateViewDropdown = None
        if self.statsFolder is not None:
            self.statsFolder.remove()
            self.statsFolder = None
        if self.plotsFolder is not None:
            self.plotsFolder.remove()
            self.plotsFolder = None

    def _show_state_view_selector(self) -> None:
        if self.stateViewDropdown is not None:
            self.stateViewDropdown.remove()
            self.stateViewDropdown = None

        if self.result is None:
            return

        self.stateViewDropdown = self.server.gui.add_dropdown(
            "Tampilan State",
            ("Final State", "Initial State"),
            initial_value="Final State",
        )

        @self.stateViewDropdown.on_update
        def _(event: viser.GuiEvent) -> None:
            if self.problem is None or self.result is None:
                return
            if event.target.value == "Initial State":
                self.renderer.render(self.problem, self.result.initial_state)
            else:
                self.renderer.render(self.problem, self.result.final_state)

    def _show_stats_card(self, algorithm_name: str, result: Result) -> None:
        if self.statsFolder is not None:
            self.statsFolder.remove()
            self.statsFolder = None

        initial_obj = (
            result.objective_history[0]
            if result.objective_history
            else 0.0
        )
        total_pkgs = len(self.problem.packages) if self.problem else 0
        init_placed = len(result.initial_state.placed_package_ids)
        final_placed = len(result.final_state.placed_package_ids)

        lines = [
            f"**Algoritma:** {algorithm_name}",
            f"- **Objective Awal:** `{initial_obj:.2f}`",
            f"- **Objective Akhir:** `{result.objective_value:.2f}`",
            f"- **Durasi Pencarian:** `{result.duration:.4f} s`",
            f"- **Total Iterasi:** `{result.iterations}`",
            f"- **Paket Terangkut (Awal → Akhir):** `{init_placed}/{total_pkgs}` → `{final_placed}/{total_pkgs}`",
        ]

        # Informasi tambahan spesifik Random Restart HC
        if result.iterations_per_restart:
            lines.append(f"- **Banyak Restart:** `{result.restarts}`")
            per_restart_str = ", ".join(
                f"R{idx}: {it}"
                for idx, it in enumerate(result.iterations_per_restart)
            )
            lines.append(f"- **Iterasi per Sesi/Restart:** `{per_restart_str}`")

        # Informasi tambahan spesifik Simulated Annealing
        if result.random_walk_history or "Simulated Annealing" in algorithm_name:
            lines.append(
                f"- **Frekuensi Stuck:** `{result.stuck_frequency}`"
            )

        self.statsFolder = self.server.gui.add_folder("Statistik Hasil Pencarian")
        with self.statsFolder:
            self.server.gui.add_markdown("\n".join(lines))

    def _show_plots_card(self, algorithm_name: str, result: Result) -> None:
        if self.plotsFolder is not None:
            self.plotsFolder.remove()
            self.plotsFolder = None

        if not result.objective_history:
            return

        self.plotsFolder = self.server.gui.add_folder("Diagram Plot Iterasi")
        with self.plotsFolder:
            obj_img = self._create_line_plot_image(
                values=result.objective_history,
                title="Objective Value terhadap Iterasi",
                xlabel="Iterasi",
                ylabel="Objective Value",
                color="#2563eb",
            )
            self.server.gui.add_image(
                obj_img, label="Plot Objective Function vs Iterasi"
            )

            if result.random_walk_history:
                rw_img = self._create_line_plot_image(
                    values=result.random_walk_history,
                    title="Probabilitas e^(deltaE / T) terhadap Iterasi",
                    xlabel="Iterasi",
                    ylabel="e^(deltaE / T)",
                    color="#d97706",
                    ylim=(0.0, 1.05),
                )
                self.server.gui.add_image(
                    rw_img, label="Plot e^(deltaE / T) vs Iterasi"
                )

    def _create_line_plot_image(
        self,
        values: tuple[float, ...],
        title: str,
        xlabel: str,
        ylabel: str,
        color: str = "#2563eb",
        ylim: tuple[float, float] | None = None,
    ) -> np.ndarray:
        """Render grafik garis ke array gambar RGB uint8 untuk ditampilkan di Viser."""
        try:
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.ticker import MaxNLocator
            from PIL import Image

            fig, ax = plt.subplots(figsize=(5.0, 3.2), dpi=120)
            fig.patch.set_facecolor("#ffffff")
            ax.set_facecolor("#f8fafc")

            x_vals = list(range(len(values)))
            ax.plot(
                x_vals,
                values,
                color=color,
                linewidth=1.8,
                marker="o" if len(values) <= 25 else None,
                markersize=3.5,
            )
            ax.set_title(title, fontsize=10, fontweight="bold", pad=8)
            ax.set_xlabel(xlabel, fontsize=8.5)
            ax.set_ylabel(ylabel, fontsize=8.5)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))
            if ylim is not None:
                ax.set_ylim(*ylim)
            ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
            ax.tick_params(labelsize=8)
            fig.tight_layout()

            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            plt.close(fig)
            buf.seek(0)
            img = Image.open(buf).convert("RGB")
            return np.asarray(img, dtype=np.uint8)
        except Exception:
            # Fallback kanvas numpy murni jika matplotlib belum ter-install
            w, h = 480, 280
            canvas = np.full((h, w, 3), 248, dtype=np.uint8)
            pad_l, pad_r, pad_t, pad_b = 40, 20, 25, 30
            plot_w = w - pad_l - pad_r
            plot_h = h - pad_t - pad_b

            canvas[pad_t : h - pad_b, pad_l] = (100, 116, 139)
            canvas[h - pad_b, pad_l : w - pad_r] = (100, 116, 139)

            if len(values) == 1:
                y = pad_t + plot_h // 2
                canvas[y - 2 : y + 3, pad_l + plot_w // 2 - 2 : pad_l + plot_w // 2 + 3] = (
                    37,
                    99,
                    235,
                )
                return canvas

            v_min = ylim[0] if ylim else min(values)
            v_max = ylim[1] if ylim else max(values)
            if abs(v_max - v_min) < 1e-9:
                v_max = v_min + 1.0

            pts = []
            n = len(values)
            for i, val in enumerate(values):
                px = pad_l + int(round((i / (n - 1)) * (plot_w - 1)))
                norm_y = (val - v_min) / (v_max - v_min)
                norm_y = max(0.0, min(1.0, norm_y))
                py = (h - pad_b - 1) - int(round(norm_y * (plot_h - 1)))
                pts.append((px, py))

            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                steps = max(abs(x1 - x0), abs(y1 - y0), 1)
                for s in range(steps + 1):
                    x = int(round(x0 + (x1 - x0) * s / steps))
                    y = int(round(y0 + (y1 - y0) * s / steps))
                    if 0 <= y < h and 0 <= x < w:
                        canvas[max(0, y - 1) : min(h, y + 2), max(0, x - 1) : min(w, x + 2)] = (
                            37,
                            99,
                            235,
                        )
            return canvas

    def _show_algorithm_options(self, options: list[AlgorithmOption]) -> None:
        for handle in self.option_handles.values():
            handle.remove()
        self.option_handles.clear()

        for option in options:
            if option.kind == "number":
                handle = self.server.gui.add_number(
                    option.label,
                    initial_value=option.default,
                    min=option.minimum,
                    max=option.maximum,
                    step=option.step or 0.1,
                )
            elif option.kind == "slider":
                if option.minimum is None or option.maximum is None:
                    raise ValueError(
                        f"Slider option '{option.key}' requires minimum and maximum"
                    )
                handle = self.server.gui.add_slider(
                    option.label,
                    min=option.minimum,
                    max=option.maximum,
                    step=option.step or 0.1,
                    initial_value=option.default,
                )
            elif option.kind == "checkbox":
                handle = self.server.gui.add_checkbox(
                    option.label,
                    initial_value=option.default,
                )
            else:
                raise ValueError(f"Unsupported option type: {option.kind}")

            self.option_handles[option.key] = handle