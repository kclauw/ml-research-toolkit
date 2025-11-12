import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QLabel
)
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
import yaml
import pathlib

# ----------------- Load runs from folder -----------------
def load_runs(base_folder="experiments"):
    runs = []
    base = pathlib.Path(base_folder)
    for run_dir in base.iterdir():
        if run_dir.is_dir():
            cfg_file = run_dir / "config.yaml"
            history_file = run_dir / "history.csv"
            if cfg_file.exists() and history_file.exists():
                with open(cfg_file) as f:
                    cfg = yaml.safe_load(f)
                df = pd.read_csv(history_file)
                runs.append({"config": cfg, "history": df, "name": run_dir.name})
    return runs

# ----------------- GUI Application -----------------
class HyperparamVisualizer(QWidget):
    def __init__(self, runs):
        super().__init__()
        self.runs = runs
        self.selected_runs = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Hyperparameter Run Visualizer")
        self.setGeometry(100, 100, 1000, 600)

        layout = QHBoxLayout()
        self.setLayout(layout)

        # Left: run list
        self.run_list = QListWidget()
        for run in self.runs:
            self.run_list.addItem(run["name"])
        self.run_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.run_list, 2)

        # Right: plot
        right_layout = QVBoxLayout()
        layout.addLayout(right_layout, 5)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        right_layout.addWidget(self.canvas)

        self.plot_button = QPushButton("Plot Selected Runs")
        self.plot_button.clicked.connect(self.plot_selected)
        right_layout.addWidget(self.plot_button)

        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(self.save_plot)
        right_layout.addWidget(self.save_button)

        self.status_label = QLabel("")
        right_layout.addWidget(self.status_label)

    def plot_selected(self):
        selected_items = self.run_list.selectedItems()
        self.ax.clear()
        if not selected_items:
            self.status_label.setText("No runs selected")
            return

        for item in selected_items:
            run_name = item.text()
            run = next(r for r in self.runs if r["name"] == run_name)
            df = run["history"]
            if "step" in df.columns and "eval/return" in df.columns:
                self.ax.plot(df["step"], df["eval/return"], label=run_name)
        self.ax.set_xlabel("Step")
        self.ax.set_ylabel("Eval Return")
        self.ax.legend()
        self.canvas.draw()
        self.status_label.setText(f"Plotted {len(selected_items)} runs")

    def save_plot(self):
        filename = "plot.png"
        self.figure.savefig(filename)
        self.status_label.setText(f"Plot saved to {filename}")


# ----------------- Main -----------------
if __name__ == "__main__":
    runs = load_runs("experiments")

    app = QApplication(sys.argv)
    window = HyperparamVisualizer(runs)
    window.show()
    sys.exit(app.exec_())
