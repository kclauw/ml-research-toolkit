import os
from typing import Dict, Callable, List, Optional
import wandb
import pandas as pd
import json 

def filter_run(cfg_subset: Dict, cfg_full: Dict) -> bool:
    """
    Check if all key-value pairs in cfg_subset match cfg_full.

    Args:
        cfg_subset (Dict): Partial configuration to match.
        cfg_full (Dict): Full configuration to check against.

    Returns:
        bool: True if all keys in cfg_subset exist in cfg_full and have equal values.
    """
    for key, value in cfg_subset.items():
        if cfg_full.get(key) != value:
            return False
    return True

def download_runs(
    entity: str,
    project: str,
    get_output_folder: Callable[[Dict, str], str],
    base_folder: str = "./results",
    filter_config: Optional[Dict] = None,
    metrics_to_download: Optional[List[str]] = None,
    save_csv: bool = True,
) -> List[str]:
    """
    Download W&B runs for a given project and save their configurations and selected metrics.

    Args:
        entity (str): WandB user or team name.
        project (str): WandB project name.
        get_output_folder (Callable[[Dict, str], str]): Function to determine output folder for each run.
        base_folder (str, optional): Base folder to store results. Defaults to './results'.
        filter_config (Optional[Dict], optional): Optional dictionary to filter runs by config.
        metrics_to_download (Optional[List[str]], optional): List of metric names to download. Defaults to None (download all).
        save_csv (bool, optional): Whether to save the metrics to a CSV file. Defaults to True.

    Returns:
        List[str]: List of output folder paths for the downloaded runs.
    """
    api = wandb.Api()
    runs = api.runs(f"{entity}/{project}")
    output_folders = []

    def matches_filter(config, filter_cfg):
        """Check if run config matches filter."""
        return all(config.get(k) == v for k, v in filter_cfg.items())

    for run in runs:
        # Clean config (remove W&B internal keys)
        config = {k: v for k, v in run.config.items() if not k.startswith("_")}
        
        # Skip runs that do not match filter_config
        if filter_config and not matches_filter(config, filter_config):
            continue

        # Determine output folder
        output_folder = get_output_folder(config, base_folder)
        os.makedirs(output_folder, exist_ok=True)

        # Save config
        with open(os.path.join(output_folder, "config.json"), "w") as f:
            json.dump(config, f, indent=2)

        # Download history
        df = run.history(keys=metrics_to_download, pandas=True)
        if not df.empty and save_csv:
            df.to_csv(os.path.join(output_folder, "metrics.csv"), index=False)

        output_folders.append(output_folder)

    return output_folders