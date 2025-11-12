# ml-research-toolkit

**A reusable Python toolkit for machine learning and reinforcement learning research projects.**  

This toolkit provides modular utilities to help you **organize experiments, visualize results, load and filter data from WandB, manage cluster jobs, and reuse common helper functions** across multiple projects. It’s designed to streamline your research workflow and reduce repetitive code.

---

## Features

- **Experiment Visualization**
  - Interactive PyQt5 GUI for plotting and comparing experiment runs.
  - Toggle runs, select seeds or hyperparameter configurations, and visualize evaluation metrics.
  - Easy plotting of histories saved locally or loaded from WandB.

- **WandB Integration**
  - Load and filter runs by project, entity, or hyperparameter configurations.
  - Download full run histories as Pandas DataFrames.
  - Utilities wrap WandB API for faster access and filtering, making experiment analysis simpler.

- **Cluster Tools**
  - Submit and manage jobs on clusters (e.g., SLURM).
  - Monitor logs, track job progress, and organize cluster experiments efficiently.

- **Reusable Utilities**
  - Load and save disk data (CSV, pickle, etc.).
  - Logging helpers, math/statistics functions, and other common routines used in research projects.

---

## Installation

### Install locally

Clone the repository and install in editable mode:

```bash
git clone https://github.com/kclauw/ml-research-toolkit.git
cd ml-research-toolkit
pip install -e .
