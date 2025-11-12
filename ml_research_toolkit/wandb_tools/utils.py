import os
from typing import Dict, Callable, List, Optional
import wandb
import pandas as pd


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
    filter_config: Optional[Dict] = None
) -> List[str]:
    """
    Download WandB runs for a given project and save their configurations.

    Args:
        entity (str): WandB user or team name.
        project (str): WandB project name.
        get_output_folder (Callable[[Dict, str], str]): Function to determine output folder for each run.
        base_folder (str, optional): Base folder to store results. Defaults to './results'.
        filter_config (Optional[Dict], optional): Optional dictionary to filter runs by config.

    Returns:
        List[str]: List of output folder paths for the downloaded runs.
    """
    api = wandb.Api()
    runs = api.runs(f"{entity}/{project}")
    output_folders = []

    for run in runs:
        # Clean config: remove internal keys starting with '_'
        config = {k: v for k, v in run.config.items() if not k.startswith("_")}
        
        for k, v in config.items():
            print((k, v))

        # Skip runs that do not match filter_config
        if filter_config and not filter_run(filter_config, config):
            continue
        
        # Determine output folder for this run
        output_folder = get_output_folder(config, base_folder)
        os.makedirs(output_folder, exist_ok=True)

        # Optionally, download artifacts, summaries, or other data here
        # e.g., run.summary, run.files()

        output_folders.append(output_folder)

    return output_folders

        
     